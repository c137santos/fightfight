# FightFight

FightFight! Porque mata-mata é o melhor formato de campeonatos!

## Contribuindo

Para contribuir para esse projeto.

1. Crie e ative uma nova virtualenv (opcional)
	```sh
	python -m venv venv
    source venv bin/activate
	```
2. Instale as dependências
  ```sh
  pip install -r requirements.txt
  ```
3. Suba um banco de dados no PostgreSQL para o projeto usar, exemplo com Docker:
  ```sh
  docker run -it --rm \
  	--name mata-pg \
      -p 5432:5432 \
      -e POSTGRES_PASSWORD=mata \
      -e POSTGRES_USER=mata \
      -v $(pwd)/pgdata:/var/lib/postgresql/data \
      postgres:15
  ```
4. Exporte a variável de ambiente `DATABASE_URL`
  ```sh
  export DATABASE_URL=postgresql://mata:mata@localhost/mata
  ```
5. Aplique as migrações do banco e dados
  ```sh
  flask db init
  flask db upgrade
  ```
6. Rode a API web :tada::
  ```sh
  flask run
  ```
7. Caso precise migrar alguma tabela
```
flask db upgrade
```

Para rodar pytest, é importante exportar a variável de ambiente que configura seu ambiente de teste.
Para melhor performace, você pode usar o SQLite. 
Como como TEST_DATABASE_URL="sqlite:////tmp/matamata.db"
# fightfight
