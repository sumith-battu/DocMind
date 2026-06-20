package com.docMind.endPoints.upload;

import jakarta.validation.constraints.NotBlank;

public record InitiateUploadRequest(@NotBlank String filename, long fileSize) {
}