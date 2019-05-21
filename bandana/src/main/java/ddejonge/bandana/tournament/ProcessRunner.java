package ddejonge.bandana.tournament;


public class ProcessRunner {
    public ProcessRunner() {}

    public static Process exec(String[] cmdArray, String name) {
        Process process = null;

        try {
            process = Runtime.getRuntime().exec(cmdArray);
            StreamGobbler errorGobbler = new StreamGobbler(process.getErrorStream(), name + " ERROR", true);
            StreamGobbler outputGobbler = new StreamGobbler(process.getInputStream(), name + " OUTPUT", true);
            errorGobbler.start();
            outputGobbler.start();
        } catch (Throwable e) {
            e.printStackTrace();
        }

        return process;
    }
}

