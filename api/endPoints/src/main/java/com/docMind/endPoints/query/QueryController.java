package com.docMind.endPoints.query;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/query")
public class QueryController {
	private final QueryService service;

	public QueryController(QueryService service) {
		this.service = service;
	}
	
	@PostMapping
	public QueryResponse query(@Valid @RequestBody QueryRequest request) {
		return service.search(request.question());
	}
	
	
}
