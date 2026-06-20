package com.docMind.endPoints.upload;

import java.util.List;
import java.util.UUID;

public record CompleteUploadRequest(UUID documentId, String uploadId, List<CompletePart> parts) {
}