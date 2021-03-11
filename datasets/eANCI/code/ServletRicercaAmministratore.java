package Servlet;

import java.io.IOException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import Bean.Amministratore;
import DB.DbEccezione;
import Manager.AmministratoreManager;
/**
 * La classe ServletRicercaAmministratore ricerca e restituisce i dati di un amministratore
 * La classe ServletRicercaAmministratore non ha dipendenze
 * @author Federico Cinque
 */
public class ServletRicercaAmministratore extends HttpServlet{

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		HttpSession session = richiesta.getSession();
		if(session!=null){
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				String matricola = richiesta.getParameter("matricola");
				AmministratoreManager AdM = new AmministratoreManager();
				Amministratore A = AdM.ricercaAdminByMatricola(matricola);

				if(A != null){
					richiesta.setAttribute("ris", A);
					rd = sc.getRequestDispatcher("/workers/index.jsp?func=mostra&page=datiA"); 
				}
				else{
					ris="Amministratore non trovato";
					richiesta.setAttribute("ris", ris);
					rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
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
}