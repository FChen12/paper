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
import Bean.Cittadino;
import Manager.AccessoManager;
/**
 * La classe ServletMostraAccessoA mostra i dati relativi all'accesso di un cittadino
 * La classe ServletMostraAccessoA non ha dipendenze
 * @author Federico Cinque
 */
public class ServletMostraAccessoA extends HttpServlet{
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
				if(session.getAttribute("c")!=null){
					Cittadino c = (Cittadino) session.getAttribute("c");
					login=c.ottenereLogin();
					ac = AM.ottenereAccesso(login);
					rd = sc.getRequestDispatcher("/user/home.jsp?func=mostra&page=accesso");
				}
				richiesta.setAttribute("accesso", ac);
				rd.forward(richiesta,risposta);
			}
			catch(DbEccezione e){
				ris=e.getMessage();
				richiesta.setAttribute("ris", ris);
				rd=sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
				rd.forward(richiesta,risposta);
			}
		}
		else{
			String url;
			url="/myDoc/user/home.jsp";
			risposta.sendRedirect(url);
		}
	}
}
