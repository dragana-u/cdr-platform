//todo remove when done testing backend and frontend integration
package mk.ukim.finki.cdrbackend.web;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/rest/test")
public class TestController {
    @GetMapping
    public String test() {
        return "Backend connected!";
    }
}
