package com.docMind.endPoints.query;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.docMind.endPoints.quota.QuotaService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/ask")
public class AskController {

    private final QueryService service;
    private final QuotaService quotaService;

    public AskController(QueryService service, QuotaService quotaService) {
        this.service = service;
        this.quotaService = quotaService;
    }

    @PostMapping
    public ResponseEntity<?> ask(
    		@RequestHeader(value = "X-Anonymous-Id", defaultValue = "demo-user") String anonId,
    		@Valid @RequestBody QueryRequest request) {
    	
    	if(!quotaService.tryConsume(anonId)) {
    		return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
    				.body(new LimitReachedResponse(
    						"You've used all " + quotaService.getLimit()
                            + " free questions.", quotaService.getLimit()));
    	}
    	
        return ResponseEntity.ok(service.ask(anonId, request.question()));
    }
}