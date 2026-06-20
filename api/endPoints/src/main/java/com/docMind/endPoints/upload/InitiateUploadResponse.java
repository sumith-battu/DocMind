package com.docMind.endPoints.upload;

import java.util.List;
import java.util.UUID;

public record InitiateUploadResponse(UUID documentId, String uploadId,
                                     long partSize, List<PartUrl> parts) {
}