package example;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class AuthorizationTest {
    @Test
    public void deniesOtherTenant() {
        assertEquals(403, Export.crossTenantStatus());
    }
}
