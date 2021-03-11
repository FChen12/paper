package Bean;
import java.util.Date;

/**
 * è un JavaBean che gestisce i metodi 
 * get e set degli attributi di un Cittadino
 * @author Francesco
 *
 */
public class Cittadino {
	private CartaIdentita ci;
    private int idCittadino;
    private String CodiceFiscale;
    private String Cognome;
    private String Nome;
    private Date DataNascita;
    private String LuogoNascita;
    private String Email;
    private boolean Advertise;
    private int nucleoFamiliare;
    private String Login;
    
	/**
	 * costruttore di default vuoto
	 */
	public Cittadino() {
		this.Advertise=false;
		this.CodiceFiscale="";
		this.Cognome="";
		this.DataNascita=null;
		this.LuogoNascita="";
		this.Email="";
		
		this.Login="";
		this.Nome="";
		
	}
	public Cittadino(String code,String cog,String nome,String res,String via){
		ci.settareNumero(code);
		this.Cognome=cog;
		this.Nome=nome;
		ci.settareResidenza(res);
		ci.settareVia(via);
	}
	public Cittadino(int nf,String codfis,String cog,String name,Date data,String luogo){
		this.nucleoFamiliare=nf;
		this.CodiceFiscale=codfis;
		this.Cognome=cog;
		this.Nome=name;
		this.DataNascita=data;
		this.LuogoNascita=luogo;
		
	}
		// TODO Auto-generated constructor stub
	/**
	 * costruttore parametrico che crea l'oggetto
	 * cittadino con i dati inseriti da quest'ultimo 
	 * all'atto della registrazione nel sistema comunale
	 */
	public Cittadino(int id,String cod_fis,String cognome,String nome,Date data,String luogo,String mail,boolean adv,int nf,String l){
		this.idCittadino=id;
		this.CodiceFiscale=cod_fis;
		this.Cognome=cognome;
		this.Nome=nome;
		this.DataNascita=data;
		this.LuogoNascita=luogo;
		this.Email=mail;
		this.Advertise=adv;
		this.nucleoFamiliare=nf;
		this.Login=l;
	}
	public String ottenereLogin(){
		return Login;
	}
	public void settareLogin(String log){
		Login=log;
	}
	public int ottenereIdCittadino(){
		return idCittadino;
	}
	public void settareIdCittadino(int idCittadino) {
		this.idCittadino = idCittadino;
	}
	public String ottenereCognome(){
		return Cognome;
	}
	public void settareCognome(String cognome){
		Cognome=cognome;
	}
	public String ottenereNome(){
		return Nome;
	}
	public void settareNome(String nome){
		Nome=nome;
	}
	public Date ottenereDataNascita(){
		return DataNascita;
	}
	public void settareDataNascita(Date data){
		DataNascita=data;
	}
	public void settareLuogoNascita(String luogo){
		LuogoNascita=luogo;
	}
	public String ottenereLuogoNascita(){
		return LuogoNascita;
	}
	public String ottenereEmail(){
		return Email;
	}
	public void settareEmail(String mail){
		Email=mail;
	}
	public boolean isAdvertise(){
		return Advertise;
	}
	public void settareIsAdvertise(boolean ad){
		Advertise=ad;
	}
	public void settareNucleoFamiliare(int nf)
	{
		nucleoFamiliare = nf;
	}
	public int ottenereNucleoFamiliare()
	{
		return nucleoFamiliare;
	}
	public String ottenereCodiceFiscale(){
		return CodiceFiscale;
	}
	public void settareCodiceFiscale(String cod_fis){
		CodiceFiscale=cod_fis;
	}
	public String toString(){
		return "ID : "+ottenereIdCittadino()+"\n"+
		       "Login : "+ottenereLogin()+"\n"+
		       "Codice fiscale : "+ottenereCodiceFiscale()+"\n"+
		       "Nome : "+ottenereNome()+"\n"+
		       "Cognome : "+ottenereCognome()+"\n"+
		       "Data di nascita : "+ottenereDataNascita()+"\n"+
		       "Luogo di Nascita : "+ottenereLuogoNascita()+"\n"+
		       "e-mail : "+ottenereEmail()+".\n";
	}

}

