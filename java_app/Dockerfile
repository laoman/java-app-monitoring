FROM amazoncorretto:17-alpine-jdk

WORKDIR /app

COPY App.java .

RUN javac App.java

# Create the log file so permissions are correct if we want to mount it
RUN touch app.log && chmod 666 app.log

# Keep container running without executing the app
# App will be started separately via 'docker exec' from Python
CMD ["tail", "-f", "/dev/null"]
