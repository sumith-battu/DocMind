package com.docMind.endPoints.query;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class QueryService {
	 private static final int TOP_K = 5;

	    private final RestClient restClient;
	    private final RestClient groqClient;
	    private final String groqModel;
	    private final JdbcTemplate jdbc;

	    public QueryService(@Value("${embedding.service.url}") String embeddingUrl,
	    		@Value("${groq.api.url}") String groqUrl,
                @Value("${groq.api.key}") String groqKey,
                @Value("${groq.model}") String groqModel,
                JdbcTemplate jdbc) {
			this.restClient = RestClient.builder().baseUrl(embeddingUrl).build();
			this.jdbc = jdbc;
			this.groqModel = groqModel;
			this.groqClient = RestClient.builder()
					.baseUrl(groqUrl)
					.defaultHeader("Authorization", "Bearer " + groqKey)
					.build();
		}
	    
	    public QueryResponse search(String question) {
	    	return new QueryResponse(retrieve(question));
	    }
	    
	    public AskResponse ask(String question) {
	    	List<Match> matches = retrieve(question);
	    	String answer = generateAnswer(question, matches);
	    	return new AskResponse(answer, matches);
	    }
	
	    private List<Match> retrieve(String question) {
	        EmbeddingResponse resp = restClient.post()
	                .uri("/embed")
	                .body(Map.of("text", question))
	                .retrieve()
	                .body(EmbeddingResponse.class);

	        String vector = resp.embedding().stream()
	                .map(String::valueOf)
	                .collect(Collectors.joining(",", "[", "]"));

	        String sql = """
	                SELECT c.content, d.filename,
	                       (c.embedding <=> CAST(? AS vector)) AS distance
	                FROM chunks c
	                JOIN documents d ON d.id = c.document_id
	                WHERE d.owner_id = ?
	                ORDER BY distance
	                LIMIT ?
	                """;

	        return jdbc.query(sql,
	                ps -> {
	                    ps.setString(1, vector);
	                    ps.setString(2, "demo-user");
	                    ps.setInt(3, TOP_K);
	                },
	                (rs, rowNum) -> new Match(
	                        rs.getString("content"),
	                        rs.getString("filename"),
	                        rs.getDouble("distance")));
	    }
	    
	    private String generateAnswer(String question, List<Match> matches) {
	    	String context = matches.stream()
	    			.map(m -> "Source (" + m.filename() + "):\n" + m.content())
	    			.collect(Collectors.joining("\n\n---\n\n"));
	    	
	    	String systemPrompt = """
	                You are DocMind, an assistant that answers questions about the user's documents.
	                Answer using ONLY the context passages provided. If the answer is not in the
	                context, say you don't have enough information. Be concise, and mention which
	                source you used.
	                """;

	        String userPrompt = "Context:\n" + context + "\n\nQuestion: " + question;

	        Map<String, Object> body = Map.of(
	                "model", groqModel,
	                "messages", List.of(
	                        Map.of("role", "system", "content", systemPrompt),
	                        Map.of("role", "user", "content", userPrompt)));

	        GroqResponse resp = groqClient.post()
	                .uri("/chat/completions")
	                .body(body)
	                .retrieve()
	                .body(GroqResponse.class);

	        return resp.choices().get(0).message().content();
	}
}
