package com.docMind.endPoints.document;

import java.time.Duration;
import java.time.OffsetDateTime;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.transaction.Transactional;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;

@Service
public class DocumentService {
	private final DocumentRepository repository;
	private final S3Presigner s3Presigner;
	private final String bucket;
	
	public DocumentService(DocumentRepository repository, S3Presigner s3Presigner,
			@Value("${aws.s3.bucket}")String bucket) {
		this.repository = repository;
		this.s3Presigner = s3Presigner;
		this.bucket = bucket;
	}
	
	@Transactional
	public DocumentResponse createDocument(CreateDocumentRequest request) {
		OffsetDateTime now = OffsetDateTime.now();
		
		Document doc = new Document();
		doc.setOwnerId("demo-user");
		doc.setFilename(request.filename());
		doc.setStatus("UPLOADING");
		doc.setCreatedAt(now);
		doc.setUpdatedAt(now);
		
		Document saved = repository.save(doc);
		
		String key = "documents/" + saved.getId() + "/" + saved.getFilename();
		saved.setS3Key(key);
		
		
		String uploadUrl = generateUploadUrl(key);
		return new DocumentResponse(saved.getId(), saved.getFilename(), saved.getStatus(), uploadUrl);
	}
	
	private String generateUploadUrl(String key) {
		PutObjectRequest objectRequest = PutObjectRequest.builder()
				.bucket(bucket)
				.key(key)
				.build();
		
		PutObjectPresignRequest presignRequest = PutObjectPresignRequest.builder()
				.signatureDuration(Duration.ofMinutes(10))
				.putObjectRequest(objectRequest)
				.build();
		
		return s3Presigner.presignPutObject(presignRequest).url().toString();
	}
	
}
