<!-- Extracted verbatim from SKILL.md section 'Java REST Assured Contract Validation'. Edit content in this file; SKILL.md keeps only the pointer. -->

## Java REST Assured Contract Validation

```java
// src/test/java/contracts/ApiContractTest.java
package contracts;

import io.restassured.RestAssured;
import io.restassured.module.jsv.JsonSchemaValidator;
import io.restassured.response.Response;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

public class ApiContractTest {

    @BeforeAll
    static void setup() {
        RestAssured.baseURI = System.getProperty("api.baseUrl", "http://<app-host>:<port>");
    }

    @Test
    @DisplayName("GET /api/users response matches JSON Schema")
    void getUsersResponseMatchesSchema() {
        given()
            .header("Accept", "application/json")
        .when()
            .get("/api/users")
        .then()
            .statusCode(200)
            .contentType("application/json")
            .body(JsonSchemaValidator.matchesJsonSchemaInClasspath(
                "schemas/users-list-response.json"
            ));
    }

    @Test
    @DisplayName("GET /api/users/:id response matches User schema")
    void getUserByIdMatchesSchema() {
        given()
            .header("Accept", "application/json")
            .pathParam("id", 1)
        .when()
            .get("/api/users/{id}")
        .then()
            .statusCode(200)
            .contentType("application/json")
            .body(JsonSchemaValidator.matchesJsonSchemaInClasspath(
                "schemas/user.schema.json"
            ))
            .body("id", notNullValue())
            .body("email", matchesPattern("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$"))
            .body("createdAt", matchesPattern(
                "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}"
            ));
    }

    @Test
    @DisplayName("Error responses follow standard error contract")
    void errorResponseFollowsContract() {
        given()
            .header("Accept", "application/json")
        .when()
            .get("/api/users/nonexistent")
        .then()
            .statusCode(anyOf(is(404), is(400)))
            .contentType("application/json")
            .body("error", notNullValue())
            .body("error.message", not(emptyOrNullString()))
            .body("error.code", notNullValue());
    }

    @Test
    @DisplayName("Pagination contract is consistent across endpoints")
    void paginationContractConsistency() {
        String[] paginatedEndpoints = {
            "/api/users",
            "/api/documents",
            "/api/reports"
        };

        for (String endpoint : paginatedEndpoints) {
            Response response = given()
                .queryParam("page", 1)
                .queryParam("limit", 10)
            .when()
                .get(endpoint);

            if (response.statusCode() == 200) {
                response.then()
                    .body("data", instanceOf(java.util.List.class))
                    .body("pagination.page", equalTo(1))
                    .body("pagination.limit", equalTo(10))
                    .body("pagination.total", instanceOf(Integer.class))
                    .body("pagination.totalPages", instanceOf(Integer.class));
            }
        }
    }

    @ParameterizedTest
    @ValueSource(strings = {"application/json", "application/xml"})
    @DisplayName("Content negotiation returns correct content type")
    void contentNegotiation(String acceptHeader) {
        Response response = given()
            .header("Accept", acceptHeader)
        .when()
            .get("/api/users");

        String contentType = response.getContentType();

        if (response.statusCode() == 200) {
            // If the API supports the requested format, it should return it
            assertThat(contentType, containsString(acceptHeader));
        } else if (response.statusCode() == 406) {
            // 406 Not Acceptable is the correct response for unsupported types
            assertThat(response.statusCode(), equalTo(406));
        }
    }

    @Test
    @DisplayName("Required response headers are present")
    void requiredHeadersPresent() {
        given()
            .header("Accept", "application/json")
        .when()
            .get("/api/users")
        .then()
            .statusCode(200)
            .header("Content-Type", containsString("application/json"))
            .header("X-Request-Id", notNullValue())
            .header("Cache-Control", notNullValue());
    }

    @Test
    @DisplayName("POST request validates required fields from schema")
    void postRequestValidation() {
        // Missing required fields should return 400 with specific validation errors
        given()
            .header("Content-Type", "application/json")
            .body("{\"invalid\": \"data\"}")
        .when()
            .post("/api/users")
        .then()
            .statusCode(anyOf(is(400), is(422)))
            .body("error.message", not(emptyOrNullString()));
    }

    @Test
    @DisplayName("Response field types match schema definitions")
    void responseFieldTypes() {
        given()
            .header("Accept", "application/json")
            .pathParam("id", 1)
        .when()
            .get("/api/users/{id}")
        .then()
            .statusCode(200)
            .body("id", anyOf(instanceOf(Integer.class), instanceOf(String.class)))
            .body("name", instanceOf(String.class))
            .body("email", instanceOf(String.class))
            .body("active", instanceOf(Boolean.class))
            .body("createdAt", instanceOf(String.class));
    }

    @Test
    @DisplayName("Null handling follows schema nullable definitions")
    void nullHandling() {
        Response response = given()
            .header("Accept", "application/json")
            .pathParam("id", 1)
        .when()
            .get("/api/users/{id}");

        if (response.statusCode() == 200) {
            // Non-nullable required fields should never be null
            response.then()
                .body("id", notNullValue())
                .body("email", notNullValue())
                .body("name", notNullValue());
        }
    }
}
```
