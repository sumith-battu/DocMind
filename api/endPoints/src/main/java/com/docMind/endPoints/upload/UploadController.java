package com.docMind.endPoints.upload;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/uploads")
public class UploadController {

    private final MultipartUploadService service;

    public UploadController(MultipartUploadService service) {
        this.service = service;
    }

    @PostMapping("/initiate")
    public InitiateUploadResponse initiate(
    		@RequestHeader(value = "X-Anonymous-Id", defaultValue = "demo-user") String anonId,
    		@Valid @RequestBody InitiateUploadRequest request) {
        return service.initiate(anonId,request);
    }

    @PostMapping("/complete")
    public void complete(@Valid @RequestBody CompleteUploadRequest request) {
        service.complete(request);
    }
}