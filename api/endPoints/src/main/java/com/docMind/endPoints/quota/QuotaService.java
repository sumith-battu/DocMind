package com.docMind.endPoints.quota;

import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class QuotaService {

	private final JdbcTemplate jdbc;
	private final int questionLimit;

	public QuotaService(JdbcTemplate jdbc, @Value("${anonymous.question.limit:10}") int questionLimit) {
		this.jdbc = jdbc;
		this.questionLimit = questionLimit;
	}
	
	public boolean tryConsume(String anonId) {
		String sql = """
				INSERT INTO anonymous_usage (anon_id, question_count)
				VALUES(?, 1)
				ON CONFLICT (anon_id)
				DO UPDATE SET question_count = anonymous_usage.question_count + 1,
							updated_at = now()
				WHERE anonymous_usage.question_count < ?
				RETURNING question_count
				""";
		List<Integer> result = jdbc.query(sql, 
				ps -> {
					ps.setString(1,anonId);
					ps.setInt(2,questionLimit);
				},
				(rs, rowNum) -> rs.getInt("question_count"));
		return !result.isEmpty();
	}
	
	public int getLimit() {
		return questionLimit;
	}
}
