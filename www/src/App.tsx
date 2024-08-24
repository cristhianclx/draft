import React, { useState, useEffect } from 'react';
import {
  ChakraProvider,
  Box,
  Flex,
  Input,
  IconButton,
  VStack,
  Text,
  Heading,
  useToast,
  Button,
  extendTheme,
  Image,
} from '@chakra-ui/react';
import { BrowserRouter as Router, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { SearchIcon } from '@chakra-ui/icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { darcula } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Lottie from 'react-lottie';
import animationData from './wait.json';

const theme = extendTheme({
  fonts: {
    heading: `'Lato', sans-serif`,
    body: `'Lato', sans-serif`,
  },
  styles: {
    global: {
      'html, body': {
        backgroundColor: 'gray.100',
      },
    },
  },
});

const Home = () => {
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const toast = useToast();
  const navigate = useNavigate();

  const defaultOptions = {
    loop: true,
    autoplay: true,
    animationData: animationData,
    rendererSettings: {
      preserveAspectRatio: 'xMidYMid slice',
    },
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch('/server/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ q: searchQuery }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Unknown error');
      }

      const data = await response.json();
      navigate(`/s/${data.id}/`);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex height="100vh" direction="column" backgroundColor="gray.100">
      {!loading ? (
        <Flex height="100vh" align="center" justify="center" direction="column" backgroundColor="gray.100">
          <VStack spacing={6} width="100%" padding={4}>
            <Image
              src="/static/logo.png"
              alt="Draft Logo"
              boxSize="100px" // Adjust the size of the logo here
              marginBottom={4}
            />
            <Heading as="h1" size="2xl" fontWeight="bold">
              DRAFT
            </Heading>
            <Text fontSize="xl" color="gray.700">
              Create mockup for apps with AI
            </Text>

            <Box width={['90%', '70%', '50%']}>
              <Flex
                as="form"
                borderRadius="md"
                boxShadow="md"
                overflow="hidden"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSearch();
                }}
              >
                <Input
                  variant="filled"
                  placeholder="Search"
                  size="lg"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  borderRadius="md"
                  backgroundColor="white"
                  _hover={{ boxShadow: 'lg' }}
                  _focus={{
                    backgroundColor: 'white',
                    boxShadow: 'outline',
                    borderColor: 'blue.500',
                  }}
                  fontSize="xl"
                  height="60px"
                />
                <IconButton
                  aria-label="Search"
                  icon={<SearchIcon />}
                  colorScheme="blue"
                  size="lg"
                  onClick={handleSearch}
                  borderRadius="md"
                  fontSize="xl"
                  height="60px"
                  minWidth="80px"
                />
              </Flex>
            </Box>

            <Text fontSize="sm" color="gray.600" alignSelf="center" mt={4}>
              Technologies: Python, Flask, LangChain, PingCAP / TIDB, Azure, Chakra UI, OpenVerse
            </Text>
          </VStack>
        </Flex>
      ) : (
        <Flex height="100vh" align="center" justify="center" direction="column" backgroundColor="gray.100">
          <Lottie options={defaultOptions} height={200} width={200} />
          <Text fontSize="xl" fontWeight="bold">
            Generating ...
          </Text>
        </Flex>
      )}
    </Flex>
  );
};

const ResultPage = () => {
  const { id } = useParams();
  const [code, setCode] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/server/data/${id}/`);
        const data = await response.json();
        setCode(data.script || '');
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, [id]);

  return (
    <Flex width="100%" height="100vh">
      <Box
        flex="2"
        position="relative"
        borderRight="1px solid gray"
        overflow="auto"
        padding={0}
        margin={0}
      >
        <CopyToClipboard text={code}>
          <Button
            position="absolute"
            top={2}
            right={2}
            colorScheme="blue"
            size="lg"
            padding="1.5rem 2rem"
            fontSize="lg"
            boxShadow="lg"
            _hover={{
              background: 'linear-gradient(90deg, rgba(33, 150, 243, 1) 0%, rgba(30, 136, 229, 1) 50%, rgba(33, 150, 243, 1) 100%)',
              boxShadow: 'xl',
            }}
          >
            Copy Code
          </Button>
        </CopyToClipboard>
        <SyntaxHighlighter
          language="javascript"
          style={darcula}
          customStyle={{ height: '100%', margin: 0, padding: '0' }}
        >
          {code}
        </SyntaxHighlighter>
      </Box>

      <Box
        flex="1"
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        padding={4}
      >
        <Text fontSize="lg" textAlign="center" marginBottom={4}>
          You can do changes in CodeSandbox.
          <br />
          To do that, you can go to CodeSandbox, fork this repository, and make changes as needed.
        </Text>
        <Button
          as="a"
          href="https://codesandbox.io/p/sandbox/draft-hf9r9y?file=%2FApp.tsx"
          target="_blank"
          colorScheme="blue"
          size="lg"
          padding="1.5rem 2rem"
          fontSize="lg"
          boxShadow="lg"
          background="linear-gradient(90deg, rgba(33, 150, 243, 1) 0%, rgba(30, 136, 229, 1) 50%, rgba(33, 150, 243, 1) 100%)"
          _hover={{
            background: 'linear-gradient(90deg, rgba(30, 136, 229, 1) 0%, rgba(33, 150, 243, 1) 50%, rgba(30, 136, 229, 1) 100%)',
            boxShadow: 'xl',
          }}
        >
          Open in CodeSandbox
        </Button>
      </Box>
    </Flex>
  );
};

const App = () => {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/s/:id/" element={<ResultPage />} />
        </Routes>
      </Router>
    </ChakraProvider>
  );
};

export default App;
