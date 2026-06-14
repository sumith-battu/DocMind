package com.docMind.endPoints.document;

import java.util.UUID;

public record DocumentResponse(
		UUID id,
		String filename,
		String status,
		String uploadUrl) {

}
