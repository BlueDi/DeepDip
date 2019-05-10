package ddejonge.bandana.tournament;

import java.io.File;
import java.io.IOException;
import java.util.*;

import ddejonge.bandana.tools.ProcessRunner;
import ddejonge.bandana.tools.Logger;


public class TournamentRunner {

	// JC: CUSTOM SETTINGS BEGIN

    final static boolean MODE = false;  //Strategy/false vs Negotiation/true
	final static int REMOTE_DEBUG = 0;	// JC: determine whether I want to remote debug the OpenAI jar or not
    private final static String GAME_MAP = "small"; // Game map can be 'standard' or 'small'
    private final static String FINAL_YEAR = "2000";

    // Using a custom map to define how many players are there on each custom map
    private final static Map<String, Integer> mapToNumberOfPlayers  = new HashMap<String, Integer>() {{
        put("standard", 7);
        put("small", 2);
    }};

	// Main folder where all the logs are stored. For each tournament a new folder will be created inside this folder
	// where the results of the tournament will be logged.
	final static String LOG_FOLDER = "log";

	//Command lines to start the various agents provided with the Bandana framework.
	// Add your own line here to run your own bot.
	final static String[] randomBotCommand = {"java", "-jar", "agents/RandomBot.jar", "-log", LOG_FOLDER, "-name", "RandomBot", "-fy", FINAL_YEAR};
	final static String[] randomNegotiatorCommand = {"java", "-jar", "agents/RandomNegotiator.jar", "-log", LOG_FOLDER, "-name", "RandomNegotiator", "-fy", FINAL_YEAR};
	final static String[] dumbBot_1_4_Command = {"java", "-jar", "agents/DumbBot-1.4.jar", "-log", LOG_FOLDER, "-name", "DumbBot", "-fy", FINAL_YEAR};
	final static String[] dbrane_1_1_Command = {"java", "-jar", "agents/D-Brane-1.1.jar", "-log", LOG_FOLDER, "-name", "D-Brane", "-fy", FINAL_YEAR};
	final static String[] dbraneExampleBotCommand = {"java", "-jar", "agents/D-BraneExampleBot.jar", "-log", LOG_FOLDER, "-name", "DBraneExampleBot", "-fy", };
	final static String[] openAIBotNegotiatorCommand = {"java", "-jar", "target/open-ai-negotiator-0.1-shaded.jar", "-log", LOG_FOLDER, "-name", "OpenAINegotiator", "-fy", FINAL_YEAR};
	final static String[] deepDipCommand = {"java", "-jar", "target/DeepDip-0.1-shaded.jar", "-log", LOG_FOLDER, "-name", "DeepDip", "-fy", FINAL_YEAR};
	final static String[] anacExampleBotCommand = {"java", "-jar", "agents/AnacExampleNegotiator.jar", "-log", LOG_FOLDER, "-name", "AnacExampleNegotiator", "-fy", FINAL_YEAR};


    // This command allows a remote debugger to connect to the .jar file JVM, allowing debugging in runtime
    final static String[] openAIBotNegotiatorCommandDebug = {"java", "-agentlib:jdwp=transport=dt_socket,server=n,address=5005,suspend=y", "-jar", "target/open-ai-negotiator-0.1-shaded.jar", "-log", "log", "-name", "OpenAINegotiator", "-fy", FINAL_YEAR};
	
	public static void main(String[] args) throws IOException {
		
		int numberOfGames = 1;				//The number of games this tournament consists of.
		
		int deadlineForMovePhases = 1; 	//60 seconds for each SPR and FAL phases
		int deadlineForRetreatPhases = 3;  //30 seconds for each SUM and AUT phases
		int deadlineForBuildPhases = 3;  	//30 seconds for each WIN phase
		
		String finalYear = FINAL_YEAR; 	//The year after which the agents in each game are supposed to propose a draw to each other. 
		// (It depends on the implementation of the players whether this will indeed happen or not, so this may not always work.) 

        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                if (MODE) {
                    NegoServerRunner.stop();
                }
                ParlanceRunner.stop();
            }
        });

		run(numberOfGames, deadlineForMovePhases, deadlineForRetreatPhases, deadlineForBuildPhases, finalYear);
	}
	
	
	static List<Process> players = new ArrayList<Process>();
	
	public static void run(int numberOfGames, int moveTimeLimit, int retreatTimeLimit, int buildTimeLimit, String finalYear) throws IOException{

        TournamentObserver tournamentObserver = null;

        try {
            // JC: get number of participants from GAME_MAP
            int numberOfParticipants = mapToNumberOfPlayers.get(GAME_MAP);

            //Create a folder to store all the results of the tournament.
            // This folder will be placed inside the LOG_FOLDER and will have the current date and time as its name.
            // You can change this line if you prefer it differently.
            String tournamentLogFolderPath = LOG_FOLDER + File.separator + Logger.getDateString();
            File logFile = new File(tournamentLogFolderPath);
            logFile.mkdirs();


            //1. Run the Parlance game server.
            ParlanceRunner.runParlanceServer(GAME_MAP, numberOfGames, moveTimeLimit, retreatTimeLimit, buildTimeLimit);

            //Create a list of ScoreCalculators to determine how the players should be ranked in the tournament.
            ArrayList<ScoreCalculator> scoreCalculators = new ArrayList<ScoreCalculator>();

            if(GAME_MAP.toLowerCase().equals("standard")) {
                scoreCalculators.add(new SoloVictoryCalculator());
                scoreCalculators.add(new SupplyCenterCalculator());
                scoreCalculators.add(new PointsCalculator());
                scoreCalculators.add(new RankCalculator());
            }
            else {
                scoreCalculators.add(new RankCalculator());
            }

            //2. Create a TournamentObserver to monitor the games and accumulate the results.
            // JC: Use "windowless = true" to run without any Diplomacy Monitor and, hence, being able to run on a server
            tournamentObserver = new TournamentObserver(tournamentLogFolderPath, scoreCalculators, numberOfGames, numberOfParticipants, true);

            //3. Run the Negotiation Server.
            if (MODE) {
                NegoServerRunner.run(tournamentObserver, tournamentLogFolderPath, numberOfGames);
            }

            for (int gameNumber = 1; gameNumber <= numberOfGames; gameNumber++) {
                if (MODE) {
                    NegoServerRunner.notifyNewGame(gameNumber);
                }

                //4. Start the players:
                for (int i = 0; i < numberOfParticipants; i++) {

                    String name;
                    String[] command;

                    //make sure that each player has a different name.
                    if (i < numberOfParticipants - 1) {
                        name = "RandomBot " + i;
                        command = randomBotCommand;
                    } else {
                        name = "DeepDip " + i;
                        command = deepDipCommand;
                    }

                    //set the log folder for this agent to be a subfolder of the tournament log folder.
                    command[4] = tournamentLogFolderPath + File.separator + name + File.separator + "Game " + gameNumber + File.separator;

                    //set the name of the agent.
                    command[6] = name;

                    //set the year after which the agent will propose a draw to the other agents.
                    command[8] = finalYear;

                    // JC: If debug is on and the current command is a OpenAINegotiator, then change the command to allow debug
                    // This is here, because otherwise we would need to change how the cycle reads the arguments
                    if (Arrays.equals(command, openAIBotNegotiatorCommand) && REMOTE_DEBUG != 0) {
                        command = openAIBotNegotiatorCommandDebug;
                    }

                    //start the process
                    String processName = name;
                    Process playerProcess = ProcessRunner.exec(command, processName);
                    // We give  a name to the process so that we can see in the console where its output comes from.
                    // This name does not have to be the same as the name given to the agent, but it would be confusing
                    // to do otherwise.

                    //store the Process object in a list.
                    players.add(playerProcess);
                }

                //5. Let the tournament observer (re-)connect to the game server.
                tournamentObserver.connectToServer();

                //NOW WAIT TILL THE GAME IS FINISHED
                while (tournamentObserver.getGameStatus() == TournamentObserver.GAME_ACTIVE || tournamentObserver.getGameStatus() == TournamentObserver.CONNECTED_WAITING_TO_START) {

                    try {
                        Thread.sleep(499);
                    } catch (InterruptedException e) {
                        System.err.println("Failed sleep" + e);
                    }

                    if (tournamentObserver.playerFailed()) {
                        // One or more players did not send its orders in in time.
                        System.err.println("A player failed to send its orders in time.");
                    }
                }
            }
        }
	    finally {
            //Kill the player processes.
            // (if everything is implemented okay this isn't necessary because the players should kill themselves. But just to be sure..)
            for (Process playerProcess : players) {
                playerProcess.destroy();
            }

            if(tournamentObserver != null){
                tournamentObserver.exit();
            }

            ParlanceRunner.stop();
            if (MODE) {
                NegoServerRunner.stop();
            }
        }
	}
}
