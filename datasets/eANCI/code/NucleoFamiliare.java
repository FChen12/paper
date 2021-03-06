package Bean;


/**
 * Questa classe si occupa di gestire lo stato di famiglia del cittadino
 * @author Christian Ronca
 *
 */
public class NucleoFamiliare {
	private int idNucleoFamiliare;
	private int capoFamiglia;
	private String nota;
	private int nComponenti;
	
	/**
	 * Costruttore standard
	 */
	public NucleoFamiliare() {
		
	}
	
	
	/**
	 * 
	 * @param idNucleoFamiliare		contiene l'id del gruppo familiare
	 * @param capofamiglia			contiene l'id del capofamiglia
	 * @param nota					eventuale nota
	 */
	public NucleoFamiliare(int idNucleoFamiliare, int capofamiglia, String nota, int nc) {
		this.idNucleoFamiliare = idNucleoFamiliare;
		this.capoFamiglia = capofamiglia;
		this.nota = nota;
		this.nComponenti=nc;
	}
	
	/**
	 * Restituisce l'id dello stato di famiglia
	 * @return	una stringa che contiene l'id dello stato di famiglia
	 */
	public int ottenereIdNucleoFamiliare() {
		return idNucleoFamiliare;
	}
	
	
	/**
	 * Setta l'id dello stato di famiglia
	 * @return	una stringa che contiene il nuovo id dello stato di famiglia
	 */
	public int settareIdNucleoFamiliare(int str) {
		idNucleoFamiliare = str;
		return idNucleoFamiliare;
	}
	
	
	/**
	 * Restituisce l'id del capofamiglia
	 * @return	una stringa che contiene l'id del capofamiglia
	 */
	public int ottenereCapoFamiglia() {
		return capoFamiglia;
	}
	
	
	/**
	 * Setta l'id del capofamiglia
	 * @return	una stringa che contiene il nuovo id del capofamiglia
	 */
	public int settareCapoFamiglia(int str) {
		capoFamiglia = str;
		return capoFamiglia;
	}
	
	
	/**
	 * Restituisce le note rilasciate
	 * @return	una stringa che contiene una nota rilasciata in precedenza
	 */
	public String ottenereNote() {
		return nota;
	}
	
	
	/**
	 * Inserisce una nota
	 * @return	una stringa che contiene la nota rilasciata
	 */
	public String settareNote(String str) {
		nota = str;
		return nota;
	}
	/**
	 * Restituisce il numero di componenti della famiglia
	 * @return	un intero che contiene il numero di componenti del nucleo familiare
	 */
	public int ottenereNComponenti() {
		return nComponenti;
	}
	
	
	/**
	 * Setta il numero di componenti del nucleo familiare
	 * @return	un intero che contiene il nuovo numero di componenti del nucleo familiare
	 */
	public int settareNComponenti(int str) {
		nComponenti = str;
		return nComponenti;
	}
}