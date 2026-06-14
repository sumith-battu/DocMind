package com.docMind.endPoints;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.jdbc.autoconfigure.DataSourceAutoConfiguration;

@SpringBootApplication
public class EndPointsApplication {

	public static void main(String[] args) {
		SpringApplication.run(EndPointsApplication.class, args);
	}

}
