package com.docMind.endPoints.document;

import jakarta.validation.constraints.NotBlank;

public record CreateDocumentRequest(
		@NotBlank String filename,
		String contentType) {}
