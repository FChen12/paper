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
import Manager.ImpiegatoManager;
import Bean.Accesso;
import Bean.Impiegato;
import DB.DbEccezione;
/**
 * La classe ServletEliminaImpiegato ricerca ed elimina un impiegato
 * La classe ServletEliminaImpiegato non ha dipendenze
 * @author Federico Cinque
 */
public class ServletEliminaImpiegato extends HttpServlet{

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException{
		HttpSession session = richiesta.getSession();
		if(session!=null){	//Se la sessione è nulla effettua il redirect alla pagina di autenticazione
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				//Se gli attributi di sessione amm e acc sono nulli devo effettuare la ricerca
				if(session.getAttribute("amm")==null && session.getAttribute("acc")==null){
					String matricola = (String) richiesta.getParameter("matricola");
					ImpiegatoManager IM = new ImpiegatoManager();
					Impiegato imp = IM.ricercaImpiegatoByMatricola(matricola);
					if(imp != null){
					session.setAttribute("amm", imp);

					AccessoManager AM = new AccessoManager();
					Accesso ac = AM.ottenereAccesso(imp.ottenereLogin());
					session.setAttribute("acc", ac);

					rd = sc.getRequestDispatcher("/workers/index.jsp?func=cancella&page=impiegato"); 
					rd.forward(richiesta,risposta);
					}
					else{
						ris="La matricola non corrisponde ad un impiegato";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita"); 
						rd.forward(richiesta,risposta);
					}
				}
				else{	//Se gli attributi sono presenti procedo con la cancellazione

					AccessoManager AM = new AccessoManager();
					ImpiegatoManager IM = new ImpiegatoManager();

					Impiegato imp = (Impiegato) session.getAttribute("amm");

					String matricola = imp.ottenereMatricola();
					String login = imp.ottenereLogin();
					
					if(IM.eliminaImpiegato(matricola) && AM.eliminaAccesso(login)){ //elimina l'impiegato e l'accesso 
																					//controllando che l'esito sia positivo
						ris="ok";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=riuscita"); 
					}
					else{
						ris="fallita";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
					}
					
					rd.forward(richiesta,risposta);
					session.removeAttribute("amm");
					session.removeAttribute("acc");
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
