package ddejonge.bandana.tournament;

import ddejonge.bandana.tools.DiplomacyMonitor;
import ddejonge.bandana.tools.FileIO;
import es.csic.iiia.fabregues.dip.Observer;
import es.csic.iiia.fabregues.dip.board.Power;
import es.csic.iiia.fabregues.dip.comm.IComm;
import es.csic.iiia.fabregues.dip.comm.daide.DaideComm;
import es.csic.iiia.fabregues.dip.orders.Order;

import java.io.File;
import java.io.IOException;
import java.net.InetAddress;
import java.util.ArrayList;

public class TournamentObserver extends Observer implements Runnable {

    public static final int NO_GAME_ACTIVE = 0;
    public static final int CONNECTED_WAITING_TO_START = 1;
    public static final int GAME_ACTIVE = 2;
    public static final int GAME_ENDED_WITH_SOLO = 3;
    public static final int GAME_ENDED_IN_DRAW = 4;


    IComm comm;

    /**
     * The object that stores the results of the tournament.
     */
    TournamentResult tournamentResult;

    /**
     * Determines how to sort players.
     */
    ArrayList<ScoreCalculator> scoreCalculators;

    /**
     * The file that logs the outcome of each game.
     */
    File gameResultsFile;

    /**
     * The file that logs for each player a summary of its results of the entire tournament.
     */
    File tournamentResultsFile;

    /**
     * The window that displays the progress of the game.
     */
    DiplomacyMonitor diplomacyMonitor;

    /**
     * The number of games in this tournament.
     */
    int numGames;
    int gameStatus;
    int gameNumber = 0;
    /**
     * Is set to true if the current game gets interrupted because one of the players did not send in his/her orders in time.
     */
    private boolean ccd;


    public TournamentObserver(String tournamentLogFolderPath, ArrayList<ScoreCalculator> scoreCalculators, int numGames, int numParticipants) throws IOException {
        super(tournamentLogFolderPath);

        if (numGames <= 0) {
            throw new RuntimeException("TournamentObserver.TournamentObserver() Error! The number of games must be greater than 0");
        }

        if (numParticipants <= 0) {
            throw new RuntimeException("TournamentObserver.TournamentObserver() Error! The number of participants must be greater than 0");
        }

        this.scoreCalculators = new ArrayList<ScoreCalculator>(scoreCalculators);

        this.name = "TournamentObserver";
        this.gameResultsFile = new File(tournamentLogFolderPath, "gameResults.log");
        this.gameResultsFile.createNewFile();

        this.tournamentResultsFile = new File(tournamentLogFolderPath, "tournamentResults.log");
        this.tournamentResultsFile.createNewFile();

        this.numGames = numGames;

        this.tournamentResult = new TournamentResult(numParticipants, scoreCalculators);

        this.diplomacyMonitor = new DiplomacyMonitor("TournamentObserver", numParticipants, scoreCalculators);

    }

    @Override
    public void run() {
        connectToServer();
    }

    public void connectToServer() {
        this.gameStatus = CONNECTED_WAITING_TO_START;
        this.game = null;
        this.ccd = false;

        diplomacyMonitor.setStatus("making connection.");

        //Create the connection with the game server
        InetAddress dipServerIp;
        try {

            if (comm != null) {
                comm.stop(); //close the previous connection, if any.
            }

            dipServerIp = InetAddress.getByName("localhost");
            comm = new DaideComm(dipServerIp, 16713, this.name);
            this.start(comm);


        } catch (Exception e) {
            this.gameStatus = NO_GAME_ACTIVE;
            diplomacyMonitor.setStatus("connection failed " + e);
            e.printStackTrace();
        }

        diplomacyMonitor.setStatus("waiting to start.");
    }

    /**
     * Is called from beforeNewPhase(), afterOldPhase(), handleSlo() and handleSMR().
     */
    void displayInfo() {
        diplomacyMonitor.setCurrentGameNumber(gameNumber);
        diplomacyMonitor.setNumGames(numGames);
        diplomacyMonitor.setPhase(game.getPhase(), game.getYear());

        for (Power power : game.getPowers()) {
            diplomacyMonitor.setNumSCs(power.getName(), power.getOwnedSCs().size());
        }

        if (this.gameStatus == GAME_ACTIVE) {
            diplomacyMonitor.setStatus("Game playing");
        } else if (this.gameStatus == CONNECTED_WAITING_TO_START) {
            diplomacyMonitor.setStatus("connected, waiting to start game.");
        } else if (this.gameStatus == GAME_ENDED_IN_DRAW) {
            diplomacyMonitor.setStatus("GAME ENDED IN A DRAW");
        } else if (this.gameStatus == GAME_ENDED_WITH_SOLO) {
            diplomacyMonitor.setStatus(winner + " WINS!");
        } else if (this.gameStatus == NO_GAME_ACTIVE) {
            diplomacyMonitor.setStatus("no game active");
        } else {
            diplomacyMonitor.setStatus("unknown game status: " + this.gameStatus);
        }

        diplomacyMonitor.update();
    }

    @Override
    public void init() {
        gameNumber++;
        this.gameStatus = GAME_ACTIVE;

        diplomacyMonitor.notifyNewGame();
    }

    @Override
    public void beforeNewPhase() {
        displayInfo();
    }

    @Override
    public void afterOldPhase() {
        displayInfo();
    }

    @Override
    public void receivedOrder(Order arg0) {
        // TODO Auto-generated method stub
    }

    @Override
    public void handleSlo(String winner) {  //SOLO
        this.gameStatus = GAME_ENDED_WITH_SOLO;

        super.handleSlo(winner);
        displayInfo();
    }

    /**
     * Is called when a player has lost connection or hasn't sent its orders.
     */
    @Override
    public void handleCCD(String powerName) {
        System.out.println("TournamentObserver.handleCCD() " + powerName + " did not manage to submit its orders in time.");
        ccd = true;
    }

    @Override
    public void exit() {
        this.comm.stop();
        super.exit();
        this.diplomacyMonitor.dispose();
    }

    /**
     * Is called when the game is over.
     */
    @Override
    public void handleSMR(String[] message) {
        if (this.gameStatus != GAME_ENDED_WITH_SOLO) {
            this.gameStatus = GAME_ENDED_IN_DRAW;
        }

        GameResult gameResult = new GameResult(message);

        this.tournamentResult.addResult(gameResult);

        FileIO.appendToFile(this.gameResultsFile, "game " + this.gameNumber + ": " + System.lineSeparator() + gameResult.toString());

        FileIO.overwriteFile(this.tournamentResultsFile, this.tournamentResult.toString());

        diplomacyMonitor.setTournamentResult(this.tournamentResult);

        displayInfo();

        super.handleSMR(message);
    }

    public int getGameStatus() {
        return this.gameStatus;
    }

    public ArrayList<GameResult> getGameResults() {
        return new ArrayList<GameResult>(this.tournamentResult.gameResults);
    }

    /**
     * Returns true if some player did not manage to submit its orders in time.
     *
     * @return
     */
    public boolean playerFailed() {
        return this.ccd;
    }

    public void setAgentName(String powerName, String agentName) {
        this.diplomacyMonitor.setAgentName(powerName, agentName);
    }
}
