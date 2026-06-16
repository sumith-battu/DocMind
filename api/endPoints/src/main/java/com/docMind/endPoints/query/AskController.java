package com.docMind.endPoints.query;

import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/ask")
public class AskController {

    private final QueryService service;

    public AskController(QueryService service) {
        this.service = service;
    }

    @PostMapping
    public AskResponse ask(@Valid @RequestBody QueryRequest request) {
        return service.ask(request.question());
    }
}