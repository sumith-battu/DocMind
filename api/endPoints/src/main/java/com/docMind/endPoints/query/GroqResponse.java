package com.docMind.endPoints.query;

import java.util.List;

public record GroqResponse(List<GroqChoice> choices) {

}
