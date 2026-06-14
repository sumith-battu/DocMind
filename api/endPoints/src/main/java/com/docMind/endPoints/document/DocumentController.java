package com.docMind.endPoints.document;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/documents")
public class DocumentController {
	private final DocumentService service;
	
	public DocumentController(DocumentService service) {
		this.service = service;
	}
	
	
	@PostMapping
	public ResponseEntity<DocumentResponse> create(@Valid @RequestBody CreateDocumentRequest request){
		DocumentResponse response = service.createDocument(request);
		return ResponseEntity.status(HttpStatus.CREATED).body(response);
	}
}
