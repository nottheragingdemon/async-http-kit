"""AsyncHTTPClient: many GET/POST requests at once over one aiohttp session, from plain synchronous code.

Optional part of the kit: needs aiohttp (pip install "asynchttp[aiohttp]"). The rest of the kit is standard library only.
"""
import aiohttp
import asyncio
from typing import Optional, Any, Union

class AsyncHTTPClient:
    """
    Docstring for AsyncHTTPClient
    """
    def __init__(self, timeout:int=30, max_concurrent:int=100):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent
        self.session:Optional[aiohttp.ClientSession]=None
    
    async def _create_session(self) -> None:
        """Create Aiohttp ClientSession"""
        self.session = aiohttp.ClientSession(timeout=self.timeout, trust_env=True)
    
    async def _close_session(self) -> None:
        """Close Aiohttp Client Session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _get(
            self,
            url:str,
            headers: Optional[dict[str, str]] = None,
            params:  Optional[dict[str, Any]] = None,
            cookies: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """Execute an Aiohttp get request

        Parameters
        ----------
        url:str
            URL to send request to

        headers: Optional[dict[str, str]] = None
            HTTP headers to include in request

        params:  Optional[dict[str, Any]] = None
            Query Parameters to include in the url

        cookies: Optional[dict[str, str]] = None
            Cookies to include in the request
        
        Returns
        -------
        dict
            Response data including status, body, and headers

        """

        if not self.session:
            raise RuntimeError("Session not initialised, Call _create_session() first.")
        
        async with self.session.get(
            url     = url,
            headers = headers,
            params  = params,
            cookies = cookies
        ) as response:
            try:
                body = await response.json()
            except aiohttp.ContentTypeError:
                body = await response.text()
            
            return {
                "status_code" : response.status,
                "body"        : body,
                "headers"     : dict(response.headers),
                "success"     : 200 <= response.status < 300
            }
    
    async def _post(
            self,
            url:str,
            headers: Optional[dict[str, str]] = None,
            data:    Optional[dict[str, Any]] = None,
            cookies: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """
        Execute an Aiohttp post request

        Parameters
        ----------
        url:str
            URL to send request to

        headers: Optional[dict[str, str]] = None
            HTTP headers to include in request

        data:  Optional[dict[str, Any]] = None
            JSON payload for post requests

        cookies: Optional[dict[str, str]] = None
            Cookies to include in the request
        
        Returns
        -------
        dict
            Response data including status, body, and headers
        """
        if not self.session:
            raise RuntimeError("Session not initialised, Call _create_session() first.")
        
        async with self.session.post(
            url     = url,
            headers = headers,
            json    = data or {},
            cookies = cookies
        ) as response:
            try:
                body = await response.json()
            except aiohttp.ContentTypeError:
                body = await response.text()
            
            return {
                "status_code" : response.status,
                "body"        : body,
                "headers"     : dict(response.headers),
                "success"     : 200 <= response.status < 300
            }
    
    async def _fetch(
            self,
            _id:str,
            method:str,
            url:str,
            headers:Optional[dict[str, str]] = None,
            params:Optional[dict[str, Any]] = None,
            data: Optional[dict[str, Any]] = None,
            cookies: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """
        Execute a single HTTP request (GET or POST)
        Parameters
        ----------
        _id: str
            A unique identifier for the request

        url:str
            URL to send request to

        headers: Optional[dict[str, str]] = None
            HTTP headers to include in request

        params:  Optional[dict[str, Any]] = None
            Query Parameters to include in the url
        
        data:  Optional[dict[str, Any]] = None
            JSON payload for POST requests
            
        cookies: Optional[dict[str, str]] = None
            Cookies to include in the request
        """
        method = method.lower()

        try:
            if method == "get":
                response = await self._get(
                    url = url,
                    headers=headers,
                    params=params,
                    cookies=cookies
                )
            elif method == "post":
                response = await self._post(
                    url=url,
                    headers=headers,
                    data=data,
                    cookies=cookies
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        
        
            return {
                "id":_id,
                "method":method,
                "url":url,
                "status_code": response['status_code'],
                "success": response['success'],
                "body": response['body'],
                "headers":response['headers'],
                "error":None

            }
        except Exception as E:
            return {
                "id":_id,
                "method":method,
                "url":url,
                "status_code": None,
                "success": False,
                "body": None,
                "headers": None,
                "error": {
                    "type":type(E).__name__,
                    "message":str(E)
                }

            }
    
    async def _execute_batch(
            self,
            queries:list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Execute a batch of HTTP requests
        
      
        Parameters
        ----------
        queries: list[dict[str, Any]]
            A list of queries to execute
        
        Returns
        -------
        list[dict]
            List of reponse dictionaries with results
        """
        await self._create_session()

        try:
            tasks = []
            for query in queries:
                _id     = query.get("_id")
                method  = query.get("method")
                url     = query.get("url")
                headers = query.get("headers", {})
                params  = query.get("params", {})
                data    = query.get("data", {})
                cookies = query.get("cookies", {})

                if not url:
                    # create a dummy task that returns an error
                    tasks.append(
                        asyncio.create_task(
                            asyncio.sleep(
                                0,
                                result = {
                                    "id":_id,
                                    "method":method,
                                    "url":None,
                                    "status_code": None,
                                    "success": False,
                                    "body": None,
                                    "headers":None,
                                    "error":{
                                        "type":"ValueError",
                                        "message":"URL is required"
                                    }
                                }
                            )
                        )
                    )
                    continue
                task = asyncio.create_task(
                    self._fetch(
                        _id     = _id    ,
                        method  = method ,
                        url     = url    ,
                        headers = headers,
                        params  = params ,
                        data    = data   ,
                        cookies = cookies
                    )
                )
                tasks.append(task)
            
            results =  await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            
                            "id":f"request_{i}",
                            "method":None,
                            "url":None,
                            "status_code": None,
                            "success": False,
                            "body": None,
                            "headers":None,
                            "error":{
                                "type":type(result).__name__,
                                "message":str(result)
                            }
                                
                        }
                    )
                else:
                    processed_results.append(result)
            
            return processed_results

        
        finally:
            await self._close_session()
    
    
    def execute(
            self,
            queries: Union[dict[str, Any], list[dict[str, Any]]]
     ) -> list[dict[str, Any]]:
        """
        Execute one or more HTTP requests (GET or POST)
        
        Parameters
        ----------
        queries: Union[dict[str, Any], list[dict[str, Any]]]
            Single query dict or list of query dicts. Each should contain:
            - _id:str - a unique identifier (optional, auto generated if missing)
            - method:str - HTTP method ("get" or "post", defaults to "get")
            - url:str - Target URL
            - headers: dict, optional, HTTP headers
            - params: dict, optional, Query parameters (for GET requests)
            - data: dict, optional, JSON payload (for POST requests)
            - cookies:dict, optional - Cookies
        
        Returns
        -------
        list[dict[str, Any]]
            List of response dictionaries
            - id: str
            - method:str
            - url: str
            - status_code:int or None, HTTP status code (None if request failed)
            - success: bool - True if status_code is 2xx
            - body: dict or str or None- Response Body, (parse JSON or text)
            - headers: dict = Response Headers
            = error: dict or None - Error information if request failed
        
        Examples
        --------
        GET Request
        >>> client =  AsyncHttpClient()
        >>> result = client.execute({
        ...     "_id": "get_user",
        ...     "method":"get",
        ...     "url":"https://api.example.com/user/123",
        ...     "headers":{"Authorization":"Bearer Token"}
        ... })
        >>> print(result[0]['status_code']) # 200
        >>> print(result[0]["body"])  # {"name":"John", "id":123}

        POST Request
        >>> client =  AsyncHttpClient()
        >>> result = client.execute(
        ...     {
        ...         "_id": "post_user",
        ...         "method":"post",
        ...         "url":"https://api.example.com/users/",
        ...         "data":{"id":223},
        ...         "headers":{"Authorization":"Bearer Token"}
        ...     }
        ... )
        >>> print(result[0]['status_code']) # 200
        >>> print(result[0]["body"])  # {"name":"Jane", "id":223}

        Mixed POST and GET Requests
        >>> client =  AsyncHttpClient()
        >>> results = client.execute(
        ...     [
        ...         {
        ...             "_id": "post_user",
        ...             "method":"post",
        ...             "url":"https://api.example.com/users/",
        ...             "data":{"id":223},
        ...             "headers":{"Authorization":"Bearer Token"}
        ...         },
        ...         {
        ...             "_id": "get_user",
        ...             "method":"get",
        ...             "url":"https://api.example.com/user/123",
        ...             "headers":{"Authorization":"Bearer Token"}
        ...         }
        ...     ]
        ...)
        >>> for result in results:
        ...     print(f"{result['id']}: {result['status_code']}")
        """
        # normalise input ot list
        if isinstance(queries, dict):
            queries = [queries]
        
        # Execute batch
        try:
            results = asyncio.run(self._execute_batch(queries))
            return results
        
        except Exception as E:
            raise RuntimeError(f"Failed to execute requests: {str(E)}") from E