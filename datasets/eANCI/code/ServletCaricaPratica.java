package Servlet;
import Bean.*;
import Manager.*;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

/**
 * La classe ServletCaricaPratica carica in una sessione gli oggetti Cittadino e CartaIdentita
 * La classe dipende da DbCittadino e DbCartaIdentita
 * @author Christian Ronca
 */

public class ServletCaricaPratica extends HttpServlet {
	
	public void doGet(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		int id_utente = Integer.parseInt(richiesta.getParameter("id_utente"));
		
		CittadinoManager cm = new CittadinoManager();
		Cittadino cittadino = cm.ottenereCittadinoPerId(id_utente);
		HttpSession session = richiesta.getSession();
		CIManager cim = new CIManager();
		CartaIdentita ci = cim.ottenereCartaPerIdCStri(id_utente);
		
		session.setAttribute("c", cittadino);
		session.setAttribute("ci", ci);
		
		String url="/myDoc/workers/index.jsp?func=pra&page=modulone";
		risposta.sendRedirect(url);
	}

}
