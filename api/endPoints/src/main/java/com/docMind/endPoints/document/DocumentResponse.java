package com.docMind.endPoints.document;

import java.util.UUID;

public record DocumentResponse(
		UUID id,
		String filename,
		String owner,
		String status,
		String uploadUrl) {

}
