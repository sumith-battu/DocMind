package com.docMind.endPoints.query;

import java.util.List;

public record AskResponse(String answer, List<Match> sources) {

}
