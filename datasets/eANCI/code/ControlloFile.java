package Servlet;
import javax.servlet.http.*;
import javax.servlet.*;
import java.io.*;
import com.oreilly.servlet.*;

/**
 * La classe ControlloFile gestisce l'upload di un file
 * La classe non ha nessuna dipendenza
 * @author Francesco Odierna
 */

public class ControlloFile extends HttpServlet{
	
	public void doPost(HttpServletRequest richiesta, HttpServletResponse risposta)throws ServletException,IOException{
		//instanzio le variabili
		// Il ServletContext sevirà per ricavare il MIME type del file uploadato
		ServletContext context=getServletContext();
		String forward=null;
		try
		{
			// Stabiliamo la grandezza massima del file che vogliamo uploadare
			int maxUploadFile=500000000;
			MultipartRequest multi=new MultipartRequest(richiesta, ".", maxUploadFile);
			String descrizione=multi.getParameter("text");
			File myFile=multi.getFile("myFile");
			String filePath=multi.getOriginalFileName("myFile");
			String path="C:\\RichiesteCambiResidenza\\";
			try{
				// ricaviamo i dati del file mediante un InputStream
				FileInputStream inStream=new FileInputStream(myFile);
				// stabiliamo dove andrà scritto il file
				FileOutputStream outStream=new FileOutputStream(path+myFile.getName());
				// salviamo il file nel percorso specificato
	            while(inStream.available()>0){
	            	outStream.write(inStream.read());
	            }
	         // chiudiamo gli stream
	            inStream.close();
	            outStream.close();
			}catch(FileNotFoundException e){
				e.printStackTrace();
			}catch(IOException e){
				e.printStackTrace();
			}
			forward="/workers/index.jsp?func=upload&page=done";
			// mettiamo nella request i dati così da poterli ricavare dalla jsp 
			richiesta.setAttribute("contentType", context.getMimeType(path+myFile.getName()));
			richiesta.setAttribute("text", descrizione);
			richiesta.setAttribute("path", path+myFile.getName());
			RequestDispatcher rd=richiesta.getRequestDispatcher(forward);
			rd.forward(richiesta, risposta);
		}catch(Exception e){
			e.printStackTrace();
		}
	}
}