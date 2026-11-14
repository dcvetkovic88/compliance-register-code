SELECT platform.id FROM register.arrangements AS platform JOIN platform.outbox o ON o.position = platform.id;
