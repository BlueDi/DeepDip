package cruz.agents;

import java.net.InetAddress;

import ddejonge.bandana.tournament.GameResult;
import es.csic.iiia.fabregues.dip.Observer;
import es.csic.iiia.fabregues.dip.comm.CommException;
import es.csic.iiia.fabregues.dip.comm.IComm;
import es.csic.iiia.fabregues.dip.comm.daide.DaideComm;
import es.csic.iiia.fabregues.dip.orders.Order;

/**
 * The function of the OpenAIObserver is to serve as a Diplomacy game Observer, in order to know when a certain game ends.
 *
 * Parlance sends messages with the status of the game. These messages trigger methods on the observers connected to
 * the Parlance server. In this case, the most important function is the "handleSMR" which is called when the game
 * is over and notifies the OpenAIAdapter that the game/episode has finished.
 */
public class OpenAIObserver extends Observer {

    public static final int NO_GAME_ACTIVE = 0;
    public static final int CONNECTED_WAITING_TO_START = 1;
    public static final int GAME_ACTIVE = 2;
    public static final int GAME_ENDED_WITH_SOLO = 3;
    public static final int GAME_ENDED_IN_DRAW = 4;


    IComm comm;
    OpenAIAdapter openAIAdapter;

    /**Is set to true if the current game gets interrupted because one of the players did not send in his/her orders in time.*/
    private boolean ccd;

    int gameStatus;
    int gameNumber = 0;



    public OpenAIObserver(String logPath, OpenAIAdapter openAIAdapter) {
        super(logPath);

        this.openAIAdapter = openAIAdapter;
    }


    /**
     * Connects to the Parlance server as a Daide Observer.
     */
    public void connectToServer(){

        this.gameStatus = CONNECTED_WAITING_TO_START;
        this.game = null;
        this.ccd = false;

        //Create the connection with the game server
        InetAddress dipServerIp;
        try {

            if(comm != null){
                comm.stop(); //close the previous connection, if any.
            }

            dipServerIp = InetAddress.getByName("localhost");
            comm = new DaideComm(dipServerIp, 16713, this.name);
            this.start(comm);


        } catch (Exception e) {
            this.gameStatus = NO_GAME_ACTIVE;
            e.printStackTrace();
        }
    }


    @Override
    public void init() {
        gameNumber++;
        this.gameStatus = GAME_ACTIVE;
    }

    @Override
    public void receivedOrder(Order order) {

    }

    @Override
    public void afterOldPhase() {

    }

    @Override
    public void beforeNewPhase() throws CommException {

    }


    @Override
    public void handleSlo(String winner) {

        this.gameStatus = GAME_ENDED_WITH_SOLO;

    }


    /**
     * Is called when a player has lost connection or hasn't sent its orders.
     *
     */
    @Override
    public void handleCCD(String powerName) {

    }

    @Override
    public void exit(){
        this.comm.stop();
        super.exit();
    }

    /**
     * Is called when the game is over.
     */
    @Override
    public void handleSMR(String[] message) {


        GameResult gameResult = new GameResult(message, 2);

        this.openAIAdapter.endOfGame(gameResult);

    }

    public int getGameStatus(){
        return this.gameStatus;
    }


    /**
     * Returns true if some player did not manage to submit its orders in time.
     * @return
     */
    public boolean playerFailed(){
        return this.ccd;
    }

}
