package Servlet;
import Bean.*;
import DB.*;
import java.io.IOException;
import java.util.ArrayList;
import javax.servlet.*;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * La classe ServletRicercaPratica restituisce una pratica specificata nel motore di ricerca
 * La classe dipende dalla classe DbRichieste
 * @author Christian Ronca
 */

public class ServletRicercaPratica extends HttpServlet {
	
	public void doPost(HttpServletRequest richiesta, HttpServletResponse risposta) throws ServletException, IOException {
		
		int cod = Integer.parseInt(richiesta.getParameter("codice"));
		String value = richiesta.getParameter("valore");
		
		int idp = 0, idr = 0;
		String idr_attesa="", idr_lavorazione="", idr_completato="";
		
	    ArrayList<Richiesta> arrayList;
	    Richiesta ric = null;
	    DbRichiesta dbric = null;
	    
	    try {
	    	dbric = new DbRichiesta();
	    	System.out.println("ok");
		
			if(value.equals("idp")) {
				ric = dbric.ottenereRichiestaPerId(cod);
		    	richiesta.setAttribute("ris", ric);
			} else if(value.equals("idr")) {
				arrayList = (ArrayList<Richiesta>)dbric.ottenereRichiestaPerRichiedente(cod);
		    	richiesta.setAttribute("ris", arrayList);
			} else if((value.equals("accettata")) || value.equals("rifiutata")) {
				arrayList = (ArrayList<Richiesta>)dbric.ottenereRichiestaPerStato(cod, value);
		    	richiesta.setAttribute("ris", arrayList);
			} else {
				arrayList = null;
			}

	    } catch(Exception e) {
	    	//e.getMessage().toString();
	    	e.printStackTrace();
	    }
	    
	    ServletContext sc = getServletContext(); 
		RequestDispatcher rd = sc.getRequestDispatcher("/workers/index.jsp?func=visualizza&page=DatiPratica"); 
		rd.forward(richiesta,risposta);
	}
}
