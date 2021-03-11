package Bean;


/**
 * La classe Impiegato permette solo all'amministratore la gestione degli impiegati
 * La classe Impiegato non ha dipendenze
 * @author Federico Cinque
 */
public class Impiegato {
	
	private String Nome;
	private String Cognome;
	private String Matricola;
	private String Email;
	private String Login;
	
	/**
	 * Costruttore vuoto della classe Impiegato
	 */
	public Impiegato(){
		Nome=null;
		Cognome=null;
		Matricola=null;
		Email=null;
		Login=null;
	}
	/**
	 * Costruttore della classe Impiegato
	 * @param Nome
	 * @param Cognome
	 * @param Matricola
	 * @param Email
	 * @param Login
	 */
	public Impiegato(String Nome, String Cognome,String  Matricola, String Email, String Login){
		this.Nome=Nome;
		this.Cognome=Cognome;
		this.Matricola=Matricola;
		this.Email=Email;
		this.Login=Login;
	}
	/**
	 * Metodo che restituisce il nome dell'impiegato
	 * @return Nome
	 */
	public String ottenereNome() {
		return Nome;
	}
	/**
	 * Metodo che imposta il nome dell'impiegato
	 * @param nome
	 */
	public void settareNome(String nome) {
		Nome = nome;
	}
	/**
	 * Metodo che restituisce il cognome dell'impiegato
	 * @return Cognome
	 */
	public String ottenereCognome() {
		return Cognome;
	}
	/**
	 * Metodo che imposta il cognome dell'impiegato
	 * @param cognome
	 */
	public void settareCognome(String cognome) {
		Cognome = cognome;
	}
	/**
	 * Metodo che restituisce la matricola dell'impiegato
	 * @return Matricola
	 */
	public String ottenereMatricola() {
		return Matricola;
	}
	/**
	 * Metodo che imposta  la matricola dell'impiegato
	 * @param matricola
	 */
	public void settareMatricola(String matricola) {
		Matricola = matricola;
	}
	/**
	 * Metodo che restituisce l'e-mail dell'impiegato
	 * @return Email
	 */
	public String ottenereEmail() {
		return Email;
	}
	/**
	 * Metodo che imposta l'e-mail dell'impiegato
	 * @param email
	 */
	public void settareEmail(String email) {
		Email = email;
	}
	/**
	 * Metodo che restituisce la login dell'impiegato
	 * @return Login
	 */
	public String ottenereLogin() {
		return Login;
	}
	/**
	 * Metodo che imposta la login dell'impiegato
	 * @param login
	 */
	public void settareLogin(String login) {
		Login = login;
	}
	/**
	 * Metodo che converete in una stringa le informazioni di un accesso
	 * @return String
	 */
	public String toString() {
		return "Nome: "+Nome+", Cognome: "+Cognome+", Matricola: "+Matricola+", e-mail: "+Email+", Login: "+Login;
	}
}