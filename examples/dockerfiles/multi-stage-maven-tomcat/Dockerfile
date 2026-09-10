# Two-stage build: Stage 1 compiles the WAR with the full Maven/JDK
# toolchain; Stage 2 copies ONLY the built artifact into a lean Tomcat
# runtime image. Maven, the JDK, and the source tree never reach the final
# image. See docs/DOCKERFILE_REFERENCE.md#multi-stage-builds.

# ---------- Stage 1 : Build ----------
FROM maven:3.9.9-eclipse-temurin-17 AS build

WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

# ---------- Stage 2 : Runtime ----------
FROM tomcat:11.0-jdk17-temurin

RUN rm -rf /usr/local/tomcat/webapps/*
COPY --from=build /app/target/*.war /usr/local/tomcat/webapps/ROOT.war

EXPOSE 8080

CMD ["catalina.sh", "run"]
