package ddejonge.bandana.tournament;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;

import ddejonge.bandana.tools.FileIO;


public class ParlanceRunner {

	//Relative location of the parlance environment.
	private static String PARLANCE_PATH = System.getProperty("user.dir") +
			"/init-server.sh";
	
	
	//Set this path to your home folder.
	//If set incorrectly Parlance will still work but you won't be able to change the deadlines.
	//private static String HOME_FOLDER = "C:\\Users\\30044279";
	
	//you can also try the following, but it does not seem to be working properly.
	private static String HOME_FOLDER =  System.getProperty("user.home");
	
	//Location of the config file (DO NOT CHANGE THESE TWO LINES!):
	private static final String CONFIG_FOLDER = HOME_FOLDER + File.separator + ".config";
	private static final String CONFIG_FILE_NAME = "parlance.cfg";
	
	private static Process parlanceProcess;
	
	/**
	 * Starts the game server and let it play a given number of games.
	 * Note that the players and observers have to reconnect to the server each game.
	 * 
	 * @param numGames The number of games to play.
	 * @param moveTimeLimit Deadline in seconds for move phases.
	 * @param retreatTimeLimit Deadline in seconds for retreat phases.
	 * @param buildTimeLimit Deadline in seconds for build phases.
	 * @throws IOException
	 */
	public static void runParlanceServer(String map, int numGames, int moveTimeLimit, int retreatTimeLimit, int buildTimeLimit) throws IOException{
		
		//Create the configuration file in order to set the deadlines.
		createConfigFile(moveTimeLimit, retreatTimeLimit, buildTimeLimit);

		//Check if the parlance path exists.
//		File parlanceFile = new File(PARLANCE_PATH);
//		if( ! parlanceFile.exists()){
//			System.out.println("Error! the given path to parlance does not exist: " + PARLANCE_PATH);
//			System.out.println("Please adapt the class "+ ParlanceRunner.class.getName() + " with the correct path.");
//			return;
//		}
		
		//Run parlance-server
		String[] cmd = {PARLANCE_PATH, "-g" + numGames, map};
		parlanceProcess = ProcessRunner.exec(cmd, "parlance init-server.sh");
		
    	//Note: an exception is thrown if parlance is started CORRECTLY.
    	try {
    		if (parlanceProcess == null) {
    			System.err.println("Parlance failed to start.");
    		} else {
    			System.err.println("ParlanceServer.runParlanceServer() parlance exit value: " + parlanceProcess.exitValue());
    		}
		} catch (IllegalThreadStateException ignore) {
			//System.out.println("ParlanceServer.runParlanceServer() PARLANCE SERVER STARTED");
		}
    	
	    	
	}
	
	
	public static void stop(){
		
		File configFile = new File(CONFIG_FOLDER, CONFIG_FILE_NAME);
		configFile.delete();

		parlanceProcess.destroy();
		
	}
	
	
	private static void createConfigFile(int MTL, int RTL, int BTL){
		
		//Generates the  ~/.config/parlance.cfg   file
		// which is necessary in order to change the deadlines.
		// Note that this file cannot be created in any other folder or with any other name, 
		// because this is where parlance expects to find it.
		
		
		//Create the folder.
		File configFolder = new File(CONFIG_FOLDER);
		configFolder.mkdirs();
		
		//Create the file.
		File configFile = new File(CONFIG_FOLDER, CONFIG_FILE_NAME);
		if(configFile.exists()){
			configFile.delete();
		}
		try{
			configFile.createNewFile();
		}catch(Exception e){
			e.printStackTrace();
		}
		
		
		//Create its contents.
		ArrayList<String> contents = new ArrayList<String>();
		contents.add("[game]");
		contents.add("LVL = 0");
		contents.add("MTL = " + MTL);
		contents.add("RTL = " + RTL);
		contents.add("BTL = " + BTL);
		contents.add("[server]");
		contents.add("[judge]");
		contents.add("[clients]");
		contents.add("[network]");
		contents.add("[main]");
		contents.add("[datc]");
		contents.add("[tokens]");
		contents.add("[syntax]");
		
		
		FileIO.appendToFile(configFile, contents);
		
	}
	
	
}
