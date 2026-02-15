import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.text.SimpleDateFormat;
import java.util.Date;

public class App {
    public static void main(String[] args) {
        String logFilePath = "/app/app.log";
        String message = System.getenv("LOG_MESSAGE");
        if (message == null) {
            message = "Default log message";
        }
        
        String iterationsStr = System.getenv("ITERATIONS");
        int iterations = 10;
        if (iterationsStr != null) {
            try {
                iterations = Integer.parseInt(iterationsStr);
            } catch (NumberFormatException e) {
                // ignore
            }
        }

        System.out.println("Starting Java Application...");
        System.out.println("Will run for " + iterations + " iterations.");

        try (PrintWriter writer = new PrintWriter(new FileWriter(logFilePath, true))) {
            for (int i = 1; i <= iterations; i++) {
                String timestamp = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date());
                String logEntry = String.format("[%s] Loop %d: %s", timestamp, i, message);
                
                // Write to file
                writer.println(logEntry);
                writer.flush(); // Ensure it's written immediately

                // Also print to stdout for container logs
                System.out.println(logEntry);

                // Simulate work
                try {
                    Thread.sleep(1000); 
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        
        System.out.println("Application finished.");
    }
}
