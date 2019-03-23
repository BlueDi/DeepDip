package ddejonge.bandana.tournament;

import ddejonge.bandana.tools.Logger;
import ddejonge.bandana.tools.ProcessRunner;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class TournamentRunner {
    private final static int NUMBER_OF_TOURNAMENTS = 5; //The number of games this tournament consists of.
    private final static int NUMBER_OF_GAMES = 10; //The number of games this tournament consists of.
    //The year after which the agents in each game are supposed to propose a draw to each other.
    private final static String FINAL_YEAR = "2000";
    private final static String GAME_MAP = "standard";

    //Main folder where all the logs are stored. For each tournament a new folder will be created inside this folder
    // where the results of the tournament will be logged.
    private final static String LOG_FOLDER = "log";
    private final static String LOG_FOLDER_AGENTS = "PlaceHolder";

    //Command lines to start the various agents provided with the Bandana framework.
    // Add your own line here to run your own bot.
    private final static String[] randomNegotiatorCommand = {"java", "-jar", "agents/RandomNegotiator.jar", "-log", LOG_FOLDER_AGENTS, "-name", "RandomNegotiator", "-fy", FINAL_YEAR};
    private final static String[] dumbBot_1_4_Command = {"java", "-jar", "agents/DumbBot-1.4.jar", "-log", LOG_FOLDER_AGENTS, "-name", "DumbBot", "-fy", FINAL_YEAR};
    private final static String[] dbrane_1_1_Command = {"java", "-jar", "agents/D-Brane-1.1.jar", "-log", LOG_FOLDER_AGENTS, "-name", "D-Brane", "-fy", FINAL_YEAR};
    private final static String[] dbraneExampleBotCommand = {"java", "-jar", "agents/D-BraneExampleBot.jar", "-log", LOG_FOLDER_AGENTS, "-name", "DBraneExampleBot", "-fy", FINAL_YEAR};

    //final static String[] anacExampleBotCommand = {"java", "-jar", "agents/AnacExampleNegotiator.jar", "-log", LOG_FOLDER_AGENTS, "-name", "AnacExampleNegotiator", "-fy", FINAL_YEAR};
    private final static String[] Gunma_Command = {"java", "-jar", "agents/Gunma.jar", "-log", LOG_FOLDER_AGENTS, "-name", "Gunma", "-fy", "1905"};
    private final static String[] MasterMind_Command = {"java", "-jar", "agents/MasterMind.jar", "-log", LOG_FOLDER_AGENTS, "-name", "MasterMind", "-fy", FINAL_YEAR};
    private final static String[] GamlBot_Command = {"java", "-jar", "agents/GamlBot.jar", "-log", LOG_FOLDER_AGENTS, "-name", "GamlBot", "-fy", FINAL_YEAR};

    private final static String[] RandomBot_Command = {"java", "-jar", "agents/RandomBot.jar", "-log", LOG_FOLDER_AGENTS, "-name", "RandomBot", "-fy", FINAL_YEAR};
    private final static String[] RandomBot_Exe_Command = {"java", "-jar", "agents/RandomExe.jar", "-log", LOG_FOLDER_AGENTS, "-name", "RandomExe", "-fy", FINAL_YEAR};
    private final static String[] DumbBot_Command = {"java", "-jar", "agents/DumbBot.jar", "-log", LOG_FOLDER_AGENTS, "-name", "DumbBot", "-fy", FINAL_YEAR};

    private static List<Process> players = new ArrayList<>();

    public static void main2(String[] args) throws IOException {
        for(int i = 0; i < NUMBER_OF_TOURNAMENTS; i++){
            main2(args);
        }
    }

    public static void main(String[] args) throws IOException {
        int deadlineForMovePhases = 60;    //60 seconds for each SPR and FAL phases
        int deadlineForRetreatPhases = 30;  //30 seconds for each SUM and AUT phases
        int deadlineForBuildPhases = 30;    //30 seconds for each WIN phase

        run(deadlineForMovePhases, deadlineForRetreatPhases, deadlineForBuildPhases);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            //NOTE: unfortunately, Shutdownhooks don't work on windows if the program was started in eclipse and
            // you stop it by clicking the red button (on MAC it seems to work fine).
            NegoServerRunner.stop();
            ParlanceRunner.stop();
        }));
    }

    private static void run(int moveTimeLimit, int retreatTimeLimit, int buildTimeLimit) throws IOException {
        //Create a folder to store all the results of the tournament.
        // This folder will be placed inside the LOG_FOLDER and will have the current date and time as its name.
        // You can change this line if you prefer it differently.
        String tournamentLogFolderPath = LOG_FOLDER + File.separator + Logger.getDateString();
        File logFile = new File(tournamentLogFolderPath);
        logFile.mkdirs();

        //1. Run the Parlance game server.
        ParlanceRunner.runParlanceServer(GAME_MAP, NUMBER_OF_GAMES, moveTimeLimit, retreatTimeLimit, buildTimeLimit);

        //Create a list of ScoreCalculators to determine how the players should be ranked in the tournament.
        ArrayList<ScoreCalculator> scoreCalculators = new ArrayList<>();
        scoreCalculators.add(new SoloVictoryCalculator());
        //scoreCalculators.add(new DrawVictoryCalculator());
        scoreCalculators.add(new SupplyCenterCalculator());
        scoreCalculators.add(new PointsCalculator());
        scoreCalculators.add(new RankCalculator());

        //2. Create a TournamentObserver to monitor the games and accumulate the results.
        int number_of_players = GAME_MAP == "standard" ? 7 : 2;
        TournamentObserver tournamentObserver = new TournamentObserver(tournamentLogFolderPath, scoreCalculators, NUMBER_OF_GAMES, number_of_players);

        //3. Run the Negotiation Server.
        NegoServerRunner.run(tournamentObserver, tournamentLogFolderPath, NUMBER_OF_GAMES);

        for (int gameNumber = 1; gameNumber <= NUMBER_OF_GAMES; gameNumber++) {
            System.out.println();
            System.out.println("GAME " + gameNumber);

            NegoServerRunner.notifyNewGame(gameNumber);

            //4. Start the players:
            startJARplayers(tournamentLogFolderPath, Integer.parseInt(FINAL_YEAR), gameNumber);

            //5. Let the tournament observer (re-)connect to the game server.
            tournamentObserver.connectToServer();

            //NOW WAIT TILL THE GAME IS FINISHED
            while (tournamentObserver.getGameStatus() == TournamentObserver.GAME_ACTIVE || tournamentObserver.getGameStatus() == TournamentObserver.CONNECTED_WAITING_TO_START) {
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    System.err.println("Failed sleep" + e);
                }

                if (tournamentObserver.playerFailed()) {
                    // One or more players did not send its orders in in time.
                    System.err.println("Player failed to send its orders in time.");
                }
            }

            //Kill the player processes.
            // (if everything is implemented okay this isn't necessary because the players should kill themselves. But just to be sure..)
            for (Process playerProcess : players) {
                playerProcess.destroy();
            }
        }

        System.out.println("TOURNAMENT FINISHED");

        //Get the results of all the games played in this tournament.
        // Each GameResult object contains the results of one game.
        // The tournamentObserver already automatically prints these results to a text file,
        //  as well as the processed overall results of the tournament.
        // However, you may want to do your own processing of the results, for which
        // you can use this list.
        // ArrayList<GameResult> results = tournamentObserver.getGameResults();

        try {
            Thread.sleep(4000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        tournamentObserver.exit();
        ParlanceRunner.stop();
        NegoServerRunner.stop();
    }

    private static void startJARplayers(String tournamentLogFolderPath, int finalYear, int gameNumber) {
        int number_of_players = GAME_MAP == "standard" ? 7 : 2;
        for (int i = 0; i < number_of_players; i++) {
            //PlayerCommand pc = generateAllPlayers(i);
            PlayerCommand pc = generateDumbBots(i);

            String process = pc.getProcess();
            String[] command = pc.getCommand();

            //set the log folder for this agent to be a subfolder of the tournament log folder.
            command[4] = tournamentLogFolderPath + File.separator + process + File.separator + "Game " + gameNumber + File.separator;

            //set the name of the agent.
            command[6] = process;

            //set the year after which the agent will propose a draw to the other agents.
            command[8] = "" + finalYear;

            //start the process
            Process playerProcess = ProcessRunner.exec(command, process);
            // We give  a name to the process so that we can see in the console where its output comes from.
            // This name does not have to be the same as the name given to the agent, but it would be confusing
            // to do otherwise.

            //store the Process object in a list.
            players.add(playerProcess);
        }
    }

    private static PlayerCommand generateAllPlayers(int i) {
        String process;
        String[] command;
        if (i < 1) {
            process = "D-Brane " + i;
            command = dbrane_1_1_Command;
        } else if (i < 2) {
            process = "Gunma " + i;
            command = Gunma_Command;
        } else if (i < 3) {
            process = "D-BraneExampleBot " + i;
            command = dbraneExampleBotCommand;
        /*} else if (i < 4) {
            process = "MasterMind " + i;
            command = MasterMind_Command;*/
        } else if (i < 5) {
            process = "GamlBot " + i;
            command = GamlBot_Command;
        } else if (i < 6) {
            process = "RandomNegotiator " + i;
            command = randomNegotiatorCommand;
        } else {
            process = "DumbBot " + i;
            command = dumbBot_1_4_Command;
        }
        return new PlayerCommand(process, command);
    }

    private static PlayerCommand generateRandomPlayers(int i) {
        String process;
        String[] command;
        if (i < 5) {
            process = "RandomBot " + i;
            command = RandomBot_Command;
        } else if (i < 6) {
            process = "DumbBot " + i;
            command = DumbBot_Command;
        } else {
            process = "RandomExe " + i;
            command = RandomBot_Exe_Command;
        }
        return new PlayerCommand(process, command);
    }

    private static PlayerCommand generateDumbBots(int i) {
        String process = "DumbBot " + i;
        return new PlayerCommand(process, DumbBot_Command);
    }
}
