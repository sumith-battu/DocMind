package com.docMind.endPoints.query;

import jakarta.validation.constraints.NotBlank;

public record QueryRequest(@NotBlank String question) {

}
