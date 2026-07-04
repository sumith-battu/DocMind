package com.docMind.endPoints.upload;

import com.docMind.endPoints.document.Document;
import com.docMind.endPoints.document.DocumentRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CreateMultipartUploadRequest;
import software.amazon.awssdk.services.s3.model.CreateMultipartUploadResponse;
import software.amazon.awssdk.services.s3.model.UploadPartRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.UploadPartPresignRequest;
import software.amazon.awssdk.services.s3.model.CompleteMultipartUploadRequest;
import software.amazon.awssdk.services.s3.model.CompletedMultipartUpload;
import software.amazon.awssdk.services.s3.model.CompletedPart;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class MultipartUploadService {

    private static final long PART_SIZE = 8L * 1024 * 1024; // 8 MB

    private final S3Client s3Client;
    private final S3Presigner s3Presigner;
    private final String bucket;
    private final DocumentRepository documentRepository;

    public MultipartUploadService(S3Client s3Client,
                                  S3Presigner s3Presigner,
                                  @Value("${aws.s3.bucket}") String bucket,
                                  DocumentRepository documentRepository) {
        this.s3Client = s3Client;
        this.s3Presigner = s3Presigner;
        this.bucket = bucket;
        this.documentRepository = documentRepository;
    }

    @Transactional
    public InitiateUploadResponse initiate(String ownerId,InitiateUploadRequest request) {
        OffsetDateTime now = OffsetDateTime.now();

        Document doc = new Document();
        doc.setOwnerId(ownerId);
        doc.setFilename(request.filename());
        doc.setStatus("UPLOADING");
        doc.setCreatedAt(now);
        doc.setUpdatedAt(now);
        Document saved = documentRepository.save(doc);

        String key = "documents/" + saved.getId() + "/" + saved.getFilename();
        saved.setS3Key(key);

        CreateMultipartUploadResponse created = s3Client.createMultipartUpload(
                CreateMultipartUploadRequest.builder().bucket(bucket).key(key).build());
        String uploadId = created.uploadId();

        int partCount = (int) Math.ceil((double) request.fileSize() / PART_SIZE);
        List<PartUrl> parts = new ArrayList<>();
        for (int partNumber = 1; partNumber <= partCount; partNumber++) {
            UploadPartRequest uploadPart = UploadPartRequest.builder()
                    .bucket(bucket).key(key).uploadId(uploadId).partNumber(partNumber).build();
            UploadPartPresignRequest presign = UploadPartPresignRequest.builder()
                    .signatureDuration(Duration.ofHours(1))
                    .uploadPartRequest(uploadPart).build();
            String url = s3Presigner.presignUploadPart(presign).url().toString();
            parts.add(new PartUrl(partNumber, url));
        }

        return new InitiateUploadResponse(saved.getId(), uploadId, PART_SIZE, parts);
    }
    
    @Transactional
    public void complete(CompleteUploadRequest request) {
        Document doc = documentRepository.findById(request.documentId())
                .orElseThrow(() -> new IllegalArgumentException("Document not found: " + request.documentId()));

        List<CompletedPart> completedParts = request.parts().stream()
                .map(p -> CompletedPart.builder().partNumber(p.partNumber()).eTag(p.eTag()).build())
                .toList();

        s3Client.completeMultipartUpload(CompleteMultipartUploadRequest.builder()
                .bucket(bucket)
                .key(doc.getS3Key())
                .uploadId(request.uploadId())
                .multipartUpload(CompletedMultipartUpload.builder().parts(completedParts).build())
                .build());
    }
}