package ddejonge.bandana.tournament;

import ddejonge.negoServer.Utils;

public class SupplyCenterCalculator extends ScoreCalculator{

	
	public SupplyCenterCalculator() {
		super(true);
	}


	@Override
	public double calculateGameScore(GameResult newResult, String playerName) {
		return newResult.getNumSupplyCenters(playerName);
	}

	@Override
	public double getTournamentScore(String playerName) {
		return  this.getAverageScore(playerName);
	}



	@Override
	public String getScoreSystemName() {
		return "Supply Centers";
	}

	@Override
	public String getScoreString(String playerName) {
		
		long total = Math.round(this.getTotalScore(playerName));
		double average = Utils.round(this.getAverageScore(playerName), 3);
		
		return "" + total + " (av. = "+ average + ")";
		
	}




}
