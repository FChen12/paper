package Servlet;

import java.io.IOException;
import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import Manager.AccessoManager;
import Manager.CIManager;
import Manager.CittadinoManager;
import Manager.NucleoFamiliareManager;
import Bean.Accesso;
import Bean.CartaIdentita;
import Bean.Cittadino;
import Bean.NucleoFamiliare;
import DB.DbEccezione;
/**
 * La classe ServletEliminaCittadino ricerca ed elimina un cittadino
 * La classe ServletEliminaCittadino non ha dipendenze
 * @author Federico Cinque
 */
public class ServletEliminaCittadino extends HttpServlet{

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException{
		HttpSession session = richiesta.getSession();
		if(session!=null){	//Se la sessione è nulla effettua il redirect alla pagina di autenticazione
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				//Se gli attributi di sessione c e acc sono nulli devo effettuare la ricerca
				if(session.getAttribute("c")==null && session.getAttribute("acc")==null){
					String cod = richiesta.getParameter("ci").toUpperCase();
					CIManager CIM = new CIManager();
					CittadinoManager CM = new CittadinoManager();
					CartaIdentita CI = CIM.ottenereCartaPerNumero(cod);

					if(CI!=null){
						Cittadino c = CM.ottenereCittadinoPerId(CI.id());
						session.setAttribute("c", c);

						AccessoManager AM = new AccessoManager();
						Accesso ac = AM.ottenereAccesso(c.ottenereLogin());
						session.setAttribute("acc", ac);

						NucleoFamiliareManager NFM = new NucleoFamiliareManager();
						int componenti = NFM.ottenereNComponentiNucleo(c.ottenereNucleoFamiliare());
						NucleoFamiliare nf = NFM.ottenereNucleo(c.ottenereNucleoFamiliare());
						if(componenti>1 && nf.ottenereCapoFamiglia()== c.ottenereIdCittadino()){
							String nc = "si"; 
							session.setAttribute("newCapo", nc);
						}

						sc = getServletContext();
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=cancella&page=cittadino"); 
						rd.forward(richiesta,risposta);
					}
					else{
						ris="Siamo spiacenti, il codice della carta d'identitˆ non è presente nel database";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
					}
				}
				else{//Se gli attributi sono presenti procedo con la cancellazione
					AccessoManager AM = new AccessoManager();
					CittadinoManager CM = new CittadinoManager();

					Accesso ac = (Accesso) session.getAttribute("acc");
					Cittadino c = (Cittadino) session.getAttribute("c");

					String login = ac.ottenereLogin();

					if(richiesta.getParameter("ci").equals("")){	//Se non c'è il codice della carta d'identitˆ
																//il cittadino da cancellare è solo nel nucleo familiare
						if(AM.eliminaAccesso(login) && CM.cancellaCittadino(c.ottenereIdCittadino())){	//elimina il cittadino e l'accesso 
																									//controllando che l'esito sia positivo
							NucleoFamiliareManager NFM = new NucleoFamiliareManager();
							NFM.ottenereNComponentiNucleo(c.ottenereNucleoFamiliare());
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
					else{	//Se è presente un codice devo sostituire il capo famiglia
						NucleoFamiliareManager NFM = new NucleoFamiliareManager();
						CIManager CIM = new CIManager();
						CartaIdentita CI = CIM.ottenereCartaPerNumero(richiesta.getParameter("ci")); 
						if(CI!=null){	//Controllo che il nuovo capo famiglia esiste nel db
							Cittadino newCapo = CM.ottenereCittadinoPerId(CI.id());
							NFM.settareCapoFamiglia(c.ottenereNucleoFamiliare(), newCapo.ottenereIdCittadino()); //modifico il capo famiglia del nucleo
							if(CM.cancellaCittadino(c.ottenereIdCittadino())){//elimina il cittadino e l'accesso 
																								//controllando che l'esito sia positivo
								NFM.decrementaComponenti(c.ottenereNucleoFamiliare());	// Decremento il numero di componenti del nucleo
								AM.eliminaAccesso(login);
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
						else{
							ris="Siamo spiacenti, il codice della carta d'identità del nuovo capo famiglia non è presente nel database";
							richiesta.setAttribute("ris", ris);
							rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
						}
					}
					rd.forward(richiesta,risposta);
					session.removeAttribute("c");
					session.removeAttribute("acc");
					session.removeAttribute("newCapo");
				}
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
}
