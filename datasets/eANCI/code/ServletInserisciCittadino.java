package Servlet;

import java.io.IOException;
import java.util.Date;
import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import Bean.Cittadino;
import Bean.NucleoFamiliare;
import DB.DbEccezione;
import Manager.CittadinoManager;
import Manager.NucleoFamiliareManager;
/**
 * La classe ServletInserisciCittadino inserisce un cittadino nel database
 * La classe ServletInserisciCittadino non ha dipendenze
 * @author Federico Cinque
 */
public class ServletInserisciCittadino extends HttpServlet {

	private String nome;
	private String cognome;
	private String cf;
	private int giorno;
	private int mese;
	private int anno;
	private Date dataN = new Date();
	private String luogoN;
	private String email;
	private boolean advertise;
	private int idNF;
	private String login;
	private String tipo;
	private Cittadino cittadino;
	NucleoFamiliareManager NFM;

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		HttpSession session = richiesta.getSession();
		if(session!=null){	//Se la sessione è nulla effettua il redirect alla pagina di autenticazione
			RequestDispatcher rd = null;
			ServletContext sc = getServletContext();
			String ris;
			try{
				nome = richiesta.getParameter("nome");
				cognome = richiesta.getParameter("cognome");
				cf = richiesta.getParameter("cf").toUpperCase();
				giorno = Integer.parseInt(richiesta.getParameter("gg"));
				mese = Integer.parseInt(richiesta.getParameter("mm"));
				anno = Integer.parseInt(richiesta.getParameter("aa"));
				dataN.setDate(giorno);
				dataN.setMonth(mese);
				dataN.setYear(anno);
				luogoN = richiesta.getParameter("ln");
				if(richiesta.getParameter("email")!=null)
					email = richiesta.getParameter("email");
				else
					email= "";
				advertise = false;
				idNF = Integer.parseInt(richiesta.getParameter("nucleof"));
				login = null;
				tipo = "Cittadino";

				CittadinoManager CM = new CittadinoManager();
				NFM = new NucleoFamiliareManager();

				cittadino = new Cittadino(0,cf,cognome,nome,dataN,luogoN,email,advertise,idNF,login);

				if(idNF==0){	//Se l'id del nucleo familiare è zero, devo creare un nuovo nucleo
					
					int idC = CM.inserisciCittadino(cittadino); //inserisco il cittadino nel db
					cittadino.settareIdCittadino(idC);
					idNF=creaNucleoF(); //Salvo l'id del nuovo nucleo
					cittadino.settareNucleoFamiliare(idNF); //setto l'id del nucleo del cittadino
					CM.modificaNucleoFamiliare(cittadino.ottenereIdCittadino(), idNF);
					if(idNF!=0 && idC!=0){ //Se gli id restituiti sono diversi da zero l'operazione è andata a buon fine
						ris="ok";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=riuscita"); 
					}
					else{
						ris="fallita";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
					}
				}
				else{	// Se l'id del nucleo familiare non è zero, devo aggiungere il cittadino ad un nucleo esistente
					if(NFM.controllaidFamiglia(idNF)){	//controllo l'esistenza del nucleo nel db
						NFM.incrementaComponenti(idNF);	//incremento i componenti del nucleo
						int idC=0;
						if((idC = CM.inserisciCittadino(cittadino))!=0){ //inserisco il cittadino nel db e controllo se l'esito è positivo
							cittadino.settareIdCittadino(idC);
							ris="ok";
							richiesta.setAttribute("ris", ris);
							rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=riuscita");
						}
						else{
							ris="Errore inserimento cittadino";
							richiesta.setAttribute("ris", ris);
							rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
						}
					}
					else{
						ris="Id non presente";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
					}
				}
				rd.forward(richiesta,risposta);
			}
			catch(DbEccezione e){
				ris=e.getMessage();
				richiesta.setAttribute("ris", ris);
				rd=sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
				rd.forward(richiesta,risposta);
			}
		}
		else{
			String url="/myDoc/workers/Accesso.jsp";
			risposta.sendRedirect(url);
		}
	}

	private int creaNucleoF() {
		NucleoFamiliare nf = new NucleoFamiliare();
		nf.settareCapoFamiglia(cittadino.ottenereIdCittadino());
		nf.settareIdNucleoFamiliare(0);
		nf.settareNComponenti(1);
		return NFM.inserisciNucleo(nf);
	}
}
