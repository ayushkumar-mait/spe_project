FROM maven:3.9.9-eclipse-temurin-21 AS build

WORKDIR /workspace
COPY services/order-api/pom.xml .
RUN mvn -q -DskipTests dependency:go-offline

COPY services/order-api/src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:21-jre

WORKDIR /app
COPY --from=build /workspace/target/order-api-0.1.0.jar /app/order-api.jar

EXPOSE 8000
ENTRYPOINT ["java", "-jar", "/app/order-api.jar"]
