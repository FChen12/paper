package DB;
import Bean.*;
/**
 * La classe DbEccezione viene lanciata quando si verifica un eccezione legata al db
 * @author Antonio Leone
 * @version 1.0
 */
public class DbEccezione extends RuntimeException {

	private static final long serialVersionUID = -6403170047487930045L;
	public DbEccezione()
	{
	}
	public DbEccezione(String message)
	{
		super(message);
	}
}