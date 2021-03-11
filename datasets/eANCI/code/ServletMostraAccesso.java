package Servlet;

import java.io.IOException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import Bean.Accesso;
import DB.DbEccezione;
import Manager.AccessoManager;
/**
 * La classe ServletMostraAccesso mostra i dati relativi all'accesso di un impieagto o amministratore
 * La classe ServletMostraAccesso non ha dipendenze
 * @author Federico Cinque
 */
public class ServletMostraAccesso extends HttpServlet{
	public void doGet(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		HttpSession session = richiesta.getSession();

		if(session!=null){
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
			Accesso ac = null;
			AccessoManager AM = new AccessoManager();
			String login;

			login = (String) session.getAttribute("login");
			ac = AM.ottenereAccesso(login);

			//inviare i dati
			rd = sc.getRequestDispatcher("/workers/index.jsp?func=mostra&page=accesso");

			richiesta.setAttribute("accesso", ac);
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
			String url;
			url="/myDoc/workers/Accesso.jsp";
			risposta.sendRedirect(url);
		}
	}
}
