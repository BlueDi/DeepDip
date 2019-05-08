package ddejonge.bandana.tournament;


import ddejonge.negoServer.Utils;

public class PointsCalculator extends ScoreCalculator {

	public PointsCalculator() {
		super(true);
	}

	
	@Override
	public double calculateGameScore(GameResult newResult, String playerName) {
		
		
		//If the game ended with a solo victory the winner gets 12 points, the others get 0 points.
		if(newResult.endedInSolo()){
			
			if(newResult.getSoloWinner().equals(playerName)){
				return 12;
			}else{
				return 0;
			}
			
		}
		
		//If a player is eliminated he or she gets 0 points.
		if(newResult.getYearOfElimination(playerName) != 0){
			return 0;
		}
		
		int numSurvivors = newResult.getNumSurvivors();
		if(numSurvivors == 2){
			return 6;
		}else if(numSurvivors == 3){
			return 4;
		}else if(numSurvivors == 4){
			return 3;
		}else if(numSurvivors == 5){
			return 2;
		}else if(numSurvivors == 6){
			return 2;
		}else if(numSurvivors == 7){
			return 1;
		}else{
			throw new RuntimeException("GameResult.getPoints() Error! something went wrong!");
		}
	}

	@Override
	public double getTournamentScore(String playerName) {
		return this.getAverageScore(playerName);
	}


	@Override
	public String getScoreSystemName() {
		return "Points";
	}

	@Override
	public String getScoreString(String playerName) {
		
		long total = Math.round(this.getTotalScore(playerName));
		double average = Utils.round(this.getAverageScore(playerName), 3);
		
		return "" + total + " (av. = "+ average + ")";
		
	}






}
