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
import Manager.AmministratoreManager;
import Bean.Accesso;
import Bean.Amministratore;
import DB.DbEccezione;
/**
 * La classe ServletEliminaAmministratore ricerca ed elimina un amministratore
 * La classe ServletEliminaAmministratore non ha dipendenze
 * @author Federico Cinque
 */
public class ServletEliminaAmministratore extends HttpServlet{

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException{
		HttpSession session = richiesta.getSession();
		if(session!=null){ //Se la sessione è nulla effettua il redirect alla pagina di autenticazione
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				//Se gli attributi di sessione amm e acc sono nulli devo effettuare la ricerca
				if(session.getAttribute("amm")==null && session.getAttribute("acc")==null){
					String matricola = richiesta.getParameter("matricola");
					AmministratoreManager AdM = new AmministratoreManager();
					Amministratore am = AdM.ricercaAdminByMatricola(matricola);
					if(am != null){
						session.setAttribute("amm", am);

						AccessoManager AM = new AccessoManager();
						Accesso ac = AM.ottenereAccesso(am.ottenereLogin());
						session.setAttribute("acc", ac);

						rd = sc.getRequestDispatcher("/workers/index.jsp?func=cancella&page=amministratore"); 
						rd.forward(richiesta,risposta);
					}
					else{
						ris="La matricola non corrisponde ad un amministratore";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita"); 
						rd.forward(richiesta,risposta);
					}
				}
				else{	//Se gli attributi sono presenti procedo con la cancellazione

					AccessoManager AM = new AccessoManager();
					AmministratoreManager AdM = new AmministratoreManager();

					Accesso ac = (Accesso) session.getAttribute("acc");
					Amministratore am = (Amministratore) session.getAttribute("amm");

					String matricola = am.ottenereMatricola();
					String login = ac.ottenereLogin();

					String risCanc = AdM.eliminaAmministratore(matricola);	//provo ad effettuare la cancellazione

					if(risCanc.equals("ok")){ // controllo che l'amministratore non è unico ed è stato cancellato
						if(AM.eliminaAccesso(login)){ //elimina l'accesso corrspondente
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
						if(risCanc.equals("unico")) //se l'amministratore è unico non è stato cancellato
							ris="Non si pu˜ cancellare l'ultimo amministratore";
						else
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
