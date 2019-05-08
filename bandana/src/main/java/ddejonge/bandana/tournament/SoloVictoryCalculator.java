package ddejonge.bandana.tournament;


import ddejonge.negoServer.Utils;

public class SoloVictoryCalculator extends ScoreCalculator{

	public SoloVictoryCalculator() {
		super(true);
	}
	
	@Override
	public double calculateGameScore(GameResult newResult, String playerName) {
		
		if(newResult.endedInSolo() && newResult.getSoloWinner().equals(playerName) ){
			return 1.0;
		}else{
			return 0.0;
		}
		
	}

	@Override
	public double getTournamentScore(String playerName) {
		return this.getAverageScore(playerName);
	}

	@Override
	public String getScoreSystemName() {
		return "Solo Victories";
	}

	@Override
	public String getScoreString(String playerName) {
		
		long total = Math.round(this.getTotalScore(playerName));
		double average = Utils.round(this.getAverageScore(playerName), 3);
		
		return "" + total + " (av. = "+ average + ")";
		
	}


}
