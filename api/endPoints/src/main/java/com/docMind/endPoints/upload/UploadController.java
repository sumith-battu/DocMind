package com.docMind.endPoints.upload;

import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/uploads")
public class UploadController {

    private final MultipartUploadService service;

    public UploadController(MultipartUploadService service) {
        this.service = service;
    }

    @PostMapping("/initiate")
    public InitiateUploadResponse initiate(@Valid @RequestBody InitiateUploadRequest request) {
        return service.initiate(request);
    }

    @PostMapping("/complete")
    public void complete(@Valid @RequestBody CompleteUploadRequest request) {
        service.complete(request);
    }
}