package ddejonge.bandana.tournament;

class PlayerCommand {
    private String process;
    private String[] command;

    PlayerCommand(String process, String[] command) {
        this.process = process;
        this.command = command;
    }

    String getProcess() {
        return process;
    }

    String[] getCommand() {
        return command;
    }
}
